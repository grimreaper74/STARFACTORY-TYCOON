"""Pilot pivot-preserving, uncombined import for the PR-009 gantry FBX."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = ROOT / (
    "SourceAssets/PR009/AutomatedBlankStacker/Candidate_v002/PR009_Exports/v002_candidate/"
    "SK_CA_MW_PR009_Gantry_01.fbx"
)
DEST = "/Game/LineBoss/Candidates/PressShop/PR009/DecompositionPilot_v001/Gantry"
OUT = ROOT / "Saved/Audits/press_shop_pr009_gantry_decomposition_pilot_v001.json"
EXPECTED_OBJECTS = 42
EXPECTED_LOCAL_BOUNDS_CM = {"min": [-214.0, -185.0, 216.0], "max": [214.0, 125.0, 325.0]}

library = unreal.EditorAssetLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

before_assets = set(library.list_assets(DEST, recursive=True, include_folder=False)) if library.does_directory_exist(DEST) else set()

task = unreal.AssetImportTask()
task.set_editor_properties({
    "filename": str(SOURCE),
    "destination_path": DEST,
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
properties = {
    "combine_meshes": False,
    "convert_scene": True,
    "convert_scene_unit": True,
    "generate_lightmap_u_vs": True,
    "auto_generate_collision": False,
    "remove_degenerates": True,
}
for name, value in properties.items():
    data.set_editor_property(name, value)
for optional_name, optional_value in (
    ("transform_vertex_to_absolute", False),
    ("bake_pivot_in_vertex", False),
):
    try:
        data.set_editor_property(optional_name, optional_value)
    except Exception:
        unreal.log_warning(f"PR009 decomposition pilot: unavailable FBX option {optional_name}")
task.set_editor_property("options", options)
asset_tools.import_asset_tasks([task])
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

asset_paths = sorted(library.list_assets(DEST, recursive=True, include_folder=False))
meshes = []
for asset_path in asset_paths:
    asset = library.load_asset(asset_path)
    if isinstance(asset, unreal.StaticMesh):
        meshes.append((asset_path, asset))

actors = []
records = []
mins = [float("inf")] * 3
maxs = [float("-inf")] * 3
for asset_path, mesh in meshes:
    actor = actors_api.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(600.0, -2000.0, 0.0), unreal.Rotator(yaw=-90.0))
    component = actor.static_mesh_component
    component.set_static_mesh(mesh)
    component.set_mobility(unreal.ComponentMobility.MOVABLE)
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    origin, extent = actor.get_actor_bounds(False, False)
    amin = [origin.x - extent.x, origin.y - extent.y, origin.z - extent.z]
    amax = [origin.x + extent.x, origin.y + extent.y, origin.z + extent.z]
    mins = [min(mins[index], amin[index]) for index in range(3)]
    maxs = [max(maxs[index], amax[index]) for index in range(3)]
    bounds = mesh.get_bounds()
    records.append({
        "asset": asset_path,
        "asset_name": mesh.get_name(),
        "mesh_bounds_origin_cm": [bounds.origin.x, bounds.origin.y, bounds.origin.z],
        "mesh_bounds_extent_cm": [bounds.box_extent.x, bounds.box_extent.y, bounds.box_extent.z],
        "spawned_world_bounds_cm": {"min": amin, "max": amax},
    })
    actors.append(actor)

# With the source FBX axis conversion plus station yaw -90, source local X maps
# to world -Y and source local Y maps to world -X.
expected_world = {
    "min": [600.0 - EXPECTED_LOCAL_BOUNDS_CM["max"][1], -2000.0 - EXPECTED_LOCAL_BOUNDS_CM["max"][0], EXPECTED_LOCAL_BOUNDS_CM["min"][2]],
    "max": [600.0 - EXPECTED_LOCAL_BOUNDS_CM["min"][1], -2000.0 - EXPECTED_LOCAL_BOUNDS_CM["min"][0], EXPECTED_LOCAL_BOUNDS_CM["max"][2]],
}
tolerance_cm = 1.5
bounds_match = all(
    abs(mins[index] - expected_world["min"][index]) <= tolerance_cm
    and abs(maxs[index] - expected_world["max"][index]) <= tolerance_cm
    for index in range(3)
)
count_match = len(meshes) == EXPECTED_OBJECTS
failures = []
if not count_match:
    failures.append(f"Expected {EXPECTED_OBJECTS} separate static meshes, found {len(meshes)}")
if not bounds_match:
    failures.append(f"Assembled world bounds do not reproduce source group: measured={mins,maxs} expected={expected_world}")

for actor in actors:
    actors_api.destroy_actor(actor)

status = (
    "PR009_GANTRY_UNCOMBINED_IMPORT_OBJECT_COUNT_AND_ASSEMBLED_BOUNDS_PASS__"
    "SEMANTIC_MOTION_BINDING_REQUIRED__NOT_PROMOTED"
    if not failures else "PR009_GANTRY_UNCOMBINED_IMPORT_PILOT_FAIL__NOT_PROMOTED"
)
payload = {
    "$schema": "line-boss/audit/pr009-gantry-decomposition-pilot-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": status,
    "source": str(SOURCE),
    "destination": DEST,
    "asset_count_before": len(before_assets),
    "static_mesh_count_after": len(meshes),
    "expected_object_count": EXPECTED_OBJECTS,
    "count_match": count_match,
    "assembled_world_bounds_cm": {"min": mins, "max": maxs},
    "expected_world_bounds_cm": expected_world,
    "bounds_match": bounds_match,
    "records": records,
    "failures": failures,
    "promotion_authorized": False,
    "notes": [
        "Transient actors were destroyed and no map was saved.",
        "This pilot proves import decomposition only; it does not prove pivot semantics, animation, collision, runtime or visual release quality.",
    ],
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
library.save_directory(DEST, only_if_is_dirty=False, recursive=True)
unreal.log(status)
unreal.SystemLibrary.quit_editor()
if failures:
    raise RuntimeError("; ".join(failures))
