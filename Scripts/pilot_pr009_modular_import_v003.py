"""Isolated UE 5.8 import gate for all six corrected PR-009 motion groups."""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
CANDIDATE = ROOT / "SourceAssets/PR009/AutomatedBlankStacker/Candidate_v002"
EXPORTS = CANDIDATE / "PR009_Exports/v002_candidate"
BINDING_PATH = CANDIDATE / "PR009_Audits/v002/PR009_SK_BINDING_MANIFEST_v002.json"
INTAKE_PATH = ROOT / "Saved/Audits/press_shop_pr009_source_intake_v002.json"
DEST_ROOT = "/Game/LineBoss/Candidates/PressShop/PR009/ModularImportPilot_v003"
OUT = ROOT / "Saved/Audits/press_shop_pr009_modular_import_pilot_v003.json"
STATION_LOCATION = unreal.Vector(600.0, -2000.0, 0.0)
# The FBX importer reverses source-local X inside each pivot-preserving child
# mesh.  An effective +90 world yaw reconstructs source +X across-line and
# +Y material-flow under the fixed station datum.  In the final native actor
# this is represented as the fixed -90 station yaw plus a 180 child basis.
STATION_ROTATION = unreal.Rotator(yaw=90.0)
EXPECTED_ENVELOPE = {"min": [222.5, -2259.0, 0.0], "max": [980.0, -1741.75, 326.0]}

library = unreal.EditorAssetLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def safe_asset_name(value):
    # Unreal retains hyphens in imported asset names but replaces decimal points.
    return value.replace(".", "_")


def world_location_from_source_cm(location_cm):
    source_x, source_y, source_z = location_cm
    return unreal.Vector(
        STATION_LOCATION.x - source_y,
        STATION_LOCATION.y - source_x,
        STATION_LOCATION.z + source_z,
    )


intake = json.loads(INTAKE_PATH.read_text(encoding="utf-8"))
binding = json.loads(BINDING_PATH.read_text(encoding="utf-8"))
failures = []
warnings = []
if intake.get("status") != "CANONICAL_V002_SOURCE_INTAKE_HASH_AND_MANIFEST_PASS__UNREAL_GATES_REQUIRED__NOT_PROMOTED":
    failures.append("Canonical v002 source intake is not passed")
if binding.get("status") != "PASS_NOT_PROMOTED" or binding.get("group_count") != 6:
    failures.append("Corrected six-group binding manifest is not passed")

tasks = []
group_destinations = {}
for group in binding.get("groups", []):
    source = EXPORTS / group["fbx"]
    destination = f"{DEST_ROOT}/{group['export_group']}"
    group_destinations[group["export_group"]] = destination
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(source),
        "destination_path": destination,
        "automated": True,
        "replace_existing": True,
        "replace_existing_settings": True,
        "save": True,
    })
    options = unreal.FbxImportUI()
    options.set_editor_properties({
        "import_mesh": True,
        "import_as_skeletal": False,
        "import_materials": False,
        "import_textures": False,
        "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
    })
    data = options.get_editor_property("static_mesh_import_data")
    data.set_editor_properties({
        "combine_meshes": False,
        "convert_scene": True,
        "convert_scene_unit": True,
        "generate_lightmap_u_vs": True,
        "auto_generate_collision": False,
        "remove_degenerates": True,
        "import_uniform_scale": 1.0,
    })
    for name, value in (
        ("transform_vertex_to_absolute", False),
        ("bake_pivot_in_vertex", False),
        ("force_front_x_axis", False),
    ):
        try:
            data.set_editor_property(name, value)
        except Exception as exc:
            warnings.append(f"Unavailable import option {name}: {exc}")
    task.set_editor_property("options", options)
    tasks.append(task)

if not failures:
    asset_tools.import_asset_tasks(tasks)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

all_actors = []
group_records = []
aggregate_min = [float("inf")] * 3
aggregate_max = [float("-inf")] * 3
for group in binding.get("groups", []):
    destination = group_destinations[group["export_group"]]
    expected_by_asset = {safe_asset_name(item["object_name"]): item for item in group["objects"]}
    imported = []
    for asset_path in sorted(library.list_assets(destination, recursive=True, include_folder=False)):
        asset = library.load_asset(asset_path)
        if isinstance(asset, unreal.StaticMesh):
            imported.append((asset_path, asset))
    imported_names = {asset.get_name() for _, asset in imported}
    missing_names = sorted(set(expected_by_asset) - imported_names)
    unexpected_names = sorted(imported_names - set(expected_by_asset))
    generic_names = sorted(name for name in imported_names if re.match(r"^(Cube|Cylinder|Plane|Sphere)_?\d*$", name))
    dimension_failures = []
    asset_records = []
    actors = []
    for asset_path, mesh in imported:
        expected = expected_by_asset.get(mesh.get_name())
        if expected is None:
            continue
        bounds = mesh.get_bounds()
        measured = sorted([bounds.box_extent.x * 2.0, bounds.box_extent.y * 2.0, bounds.box_extent.z * 2.0])
        expected_cm = sorted(value / 10.0 for value in expected["dimensions_mm"])
        tolerance = [max(0.25, value * 0.015) for value in expected_cm]
        if any(abs(measured[index] - expected_cm[index]) > tolerance[index] for index in range(3)):
            dimension_failures.append({
                "asset": mesh.get_name(),
                "measured_sorted_cm": measured,
                "expected_sorted_cm": expected_cm,
                "tolerance_cm": tolerance,
            })
        actor = actors_api.spawn_actor_from_class(
            unreal.StaticMeshActor,
            world_location_from_source_cm(expected["source_world"]["location_cm"]),
            STATION_ROTATION,
        )
        actor.static_mesh_component.set_static_mesh(mesh)
        actor.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE)
        actor.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        actor.set_actor_scale3d(unreal.Vector(1.0, 1.0, 1.0))
        origin, extent = actor.get_actor_bounds(False, False)
        amin = [origin.x - extent.x, origin.y - extent.y, origin.z - extent.z]
        amax = [origin.x + extent.x, origin.y + extent.y, origin.z + extent.z]
        aggregate_min = [min(aggregate_min[index], amin[index]) for index in range(3)]
        aggregate_max = [max(aggregate_max[index], amax[index]) for index in range(3)]
        actors.append(actor)
        all_actors.append(actor)
        asset_records.append({
            "asset": mesh.get_name(),
            "source_origin_cm": expected["source_world"]["location_cm"],
            "mesh_local_bounds_origin_cm": [bounds.origin.x, bounds.origin.y, bounds.origin.z],
            "mesh_local_bounds_extent_cm": [bounds.box_extent.x, bounds.box_extent.y, bounds.box_extent.z],
            "spawned_world_bounds_cm": {"min": amin, "max": amax},
        })
    group_failures = []
    if len(imported) != group["object_count"]:
        group_failures.append(f"Expected {group['object_count']} meshes, imported {len(imported)}")
    if missing_names:
        group_failures.append(f"Missing semantic assets: {missing_names}")
    if unexpected_names:
        group_failures.append(f"Unexpected assets: {unexpected_names}")
    if generic_names:
        group_failures.append(f"Generic primitive assets remain: {generic_names}")
    if dimension_failures:
        group_failures.append(f"{len(dimension_failures)} mesh dimensions exceed tolerance")
    failures.extend(f"{group['export_group']}: {message}" for message in group_failures)
    group_records.append({
        "group": group["export_group"],
        "fbx": group["fbx"],
        "expected_mesh_count": group["object_count"],
        "imported_mesh_count": len(imported),
        "semantic_names_match_after_unreal_sanitization": not missing_names and not unexpected_names,
        "missing_names": missing_names,
        "unexpected_names": unexpected_names,
        "generic_names": generic_names,
        "dimension_failure_count": len(dimension_failures),
        "dimension_failures": dimension_failures,
        "asset_records": asset_records,
        "component_scale_contract": [1.0, 1.0, 1.0],
        "failures": group_failures,
    })

assembled_within_envelope = all(
    aggregate_min[index] >= EXPECTED_ENVELOPE["min"][index] - 2.0
    and aggregate_max[index] <= EXPECTED_ENVELOPE["max"][index] + 2.0
    for index in range(3)
)
if not assembled_within_envelope:
    failures.append(
        f"Manifest-driven assembly exceeds PR-009 envelope: measured={aggregate_min, aggregate_max} expected={EXPECTED_ENVELOPE}"
    )

for actor in all_actors:
    actors_api.destroy_actor(actor)

status = (
    "PR009_CORRECTED_SIX_GROUP_UNREAL_IMPORT_SEMANTIC_NAME_SCALE_DIMENSION_AND_MANIFEST_ASSEMBLY_PASS__"
    "NATIVE_BINDING_COLLISION_NAVIGATION_AND_VISUAL_GATES_REQUIRED__NOT_PROMOTED"
    if not failures
    else "PR009_CORRECTED_SIX_GROUP_UNREAL_IMPORT_FAIL__DO_NOT_BIND_OR_PROMOTE"
)
payload = {
    "$schema": "cairnwell/audit/pr009-modular-import-pilot-v003/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": status,
    "source_candidate": str(CANDIDATE),
    "destination": DEST_ROOT,
    "import_contract": {
        "combine_meshes": False,
        "transform_vertex_to_absolute": False,
        "bake_pivot_in_vertex": False,
        "convert_scene": True,
        "convert_scene_unit": True,
        "import_uniform_scale": 1.0,
    },
    "expected_group_count": 6,
    "imported_group_count": len(group_records),
    "expected_total_mesh_count": sum(group["object_count"] for group in binding.get("groups", [])),
    "imported_total_mesh_count": sum(group["imported_mesh_count"] for group in group_records),
    "groups": group_records,
    "manifest_assembled_bounds_cm": {"min": aggregate_min, "max": aggregate_max},
    "expected_station_envelope_cm": EXPECTED_ENVELOPE,
    "assembled_within_envelope": assembled_within_envelope,
    "warnings": warnings,
    "failures": failures,
    "promotion_authorized": False,
    "notes": [
        "Transient assembly actors were destroyed and no map was modified.",
        "Unreal-invalid punctuation is compared using deterministic object-name sanitization; semantic words are retained.",
        "This gate does not prove native motion binding, collision, navigation, runtime presentation or visual release quality.",
        "Pivot-preserving children require a 180-degree relative basis under the fixed -90-degree station parent (effective +90 world yaw).",
        "PR-010 remains outside scope and untouched.",
    ],
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
library.save_directory(DEST_ROOT, only_if_is_dirty=False, recursive=True)
unreal.log(status)
unreal.SystemLibrary.quit_editor()
if failures:
    raise RuntimeError("; ".join(failures))
