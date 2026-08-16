"""Import deterministic v013 meshes and replace visuals in a fresh v027 child.

The retained native audio/runtime map is read-only.  All 336 presentation
actors keep their object identity, transform, attachment hierarchy, tags,
materials, collision, navigation, mobility and native motion bindings; only the
static-mesh asset is replaced after local-bounds parity is proven.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
STAGING_RECEIPT = ROOT / "Saved/Audits/PressTrains/press_train_a_fabrication_staging_v031.json"
STAGING_DIR = ROOT / "Saved/ImportStaging/PressTrainAFabrication_v031"
SOURCE_MANIFEST = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/AssemblyStudy_v013/PRESS_TRAIN_A_ASSEMBLY_STUDY_MANIFEST_v013.json"
BASE = "/Game/LineBoss/Maps/LB_PressTrainAAudioRuntimeCandidate_v027"
MAP = "/Game/LineBoss/Maps/LB_PressTrainAFabricationCandidate_v031"
DEST = "/Game/LineBoss/Candidates/PressTrains/TrainA/Fabrication_v031/Meshes"
BASE_FILE = ROOT / "Content/LineBoss/Maps/LB_PressTrainAAudioRuntimeCandidate_v027.umap"
MAP_FILE = ROOT / "Content/LineBoss/Maps/LB_PressTrainAFabricationCandidate_v031.umap"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_fabrication_build_v031.json"

library = unreal.EditorAssetLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def vec(value):
    return [float(value.x), float(value.y), float(value.z)]


def rot(value):
    return [float(value.pitch), float(value.yaw), float(value.roll)]


def actor_contract(actor):
    parent = actor.get_attach_parent_actor()
    component = actor.static_mesh_component
    return {
        "location": vec(actor.get_actor_location()),
        "rotation": rot(actor.get_actor_rotation()),
        "scale": vec(actor.get_actor_scale3d()),
        "parent": parent.get_actor_label() if parent else None,
        "collision_enabled": str(component.get_collision_enabled()),
        "collision_profile": str(component.get_collision_profile_name()),
        "affects_navigation": bool(component.get_editor_property("can_ever_affect_navigation")),
        "mobility": str(component.get_editor_property("mobility")),
        "cast_shadow": bool(component.get_editor_property("cast_shadow")),
        "tags": [str(value) for value in actor.tags],
    }


def mesh_size_cm(mesh):
    extent = mesh.get_bounds().box_extent
    return [float(extent.x) * 2.0, float(extent.y) * 2.0, float(extent.z) * 2.0]


receipt = json.loads(STAGING_RECEIPT.read_text(encoding="utf-8"))
manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
if receipt.get("status") != "PASS__336_DETERMINISTIC_LOCAL_PIVOT_FBX_FILES__UNREAL_IMPORT_REQUIRED__NOT_PROMOTED":
    raise RuntimeError("v031 staging receipt is not the expected PASS")
if len(receipt.get("exports", [])) != 336 or len(manifest.get("instances", [])) != 336:
    raise RuntimeError("v031 source/staging object count mismatch")
if library.does_directory_exist(DEST) or library.does_asset_exist(MAP) or OUT.exists():
    raise RuntimeError("refusing to overwrite v031 Unreal fabrication candidate")

base_hash_before = sha256(BASE_FILE)

tasks = []
for row in receipt["exports"]:
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(STAGING_DIR / row["file"]),
        "destination_path": DEST,
        "destination_name": row["asset_name"],
        "automated": True,
        "replace_existing": False,
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
        "combine_meshes": True,
        "convert_scene": True,
        "convert_scene_unit": True,
        "transform_vertex_to_absolute": False,
        "bake_pivot_in_vertex": False,
        "generate_lightmap_u_vs": True,
        "auto_generate_collision": False,
        "remove_degenerates": True,
    })
    task.set_editor_property("options", options)
    tasks.append(task)

asset_tools.import_asset_tasks(tasks)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

imported = {}
import_failures = []
for row in receipt["exports"]:
    path = f"{DEST}/{row['asset_name']}"
    mesh = library.load_asset(path)
    if not isinstance(mesh, unreal.StaticMesh):
        import_failures.append(f"missing imported mesh {path}")
        continue
    imported[row["source_object"]] = mesh
if len(imported) != 336:
    import_failures.append(f"expected 336 imported meshes, found {len(imported)}")
if import_failures:
    payload = {
        "status": "FAIL__V031_IMPORT_INCOMPLETE__NO_MAP_CREATED__NOT_A_PARENT",
        "base": BASE,
        "map": MAP,
        "destination": DEST,
        "imported_count": len(imported),
        "failures": import_failures,
        "promotion_authorized": False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    raise RuntimeError("; ".join(import_failures))

if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"could not derive {MAP} from {BASE}")

actors = actors_api.get_all_level_actors()
static_actors = [
    actor for actor in actors
    if isinstance(actor, unreal.StaticMeshActor)
    and "LB.PressTrain.ProcessDirection.PositiveY" in {str(value) for value in actor.tags}
]
if len(static_actors) != 336:
    raise RuntimeError(f"runtime child contains {len(static_actors)} train presentation actors, expected 336")

by_source = {}
for record in manifest["instances"]:
    source_name = str(record["name"])
    matches = [
        actor for actor in static_actors
        if actor.get_actor_label() == source_name
        or actor.get_actor_label().startswith(source_name + "_UE")
    ]
    if len(matches) != 1:
        raise RuntimeError(f"runtime actor identity mismatch {source_name}: {[a.get_actor_label() for a in matches]}")
    by_source[source_name] = matches[0]

contracts_before = {name: actor_contract(actor) for name, actor in by_source.items()}
replacements = []
slot_mismatches = []
bounds_mismatches = []
max_sorted_bounds_error_cm = 0.0
for source_name, actor in by_source.items():
    component = actor.static_mesh_component
    old_mesh = component.static_mesh
    new_mesh = imported[source_name]
    old_size = mesh_size_cm(old_mesh)
    new_size = mesh_size_cm(new_mesh)
    sorted_error = max(abs(a - b) for a, b in zip(sorted(old_size), sorted(new_size)))
    max_sorted_bounds_error_cm = max(max_sorted_bounds_error_cm, sorted_error)
    if sorted_error > 0.25:
        bounds_mismatches.append({
            "source_object": source_name,
            "old_size_cm": old_size,
            "new_size_cm": new_size,
            "max_sorted_error_cm": sorted_error,
        })
        continue
    old_materials = [component.get_material(index) for index in range(component.get_num_materials())]
    new_slot_count = len(new_mesh.get_editor_property("static_materials"))
    if len(old_materials) != new_slot_count:
        slot_mismatches.append({
            "source_object": source_name,
            "old_slot_count": len(old_materials),
            "new_slot_count": new_slot_count,
        })
        continue
    component.set_static_mesh(new_mesh)
    for index, material in enumerate(old_materials):
        if material is not None:
            component.set_material(index, material)
    actor.tags = list(actor.tags) + [
        unreal.Name("LB.PressTrain.Fabrication.v031"),
        unreal.Name("LB.Asset.Candidate.v031"),
        unreal.Name("LB.Asset.CandidateNotPromoted"),
    ]
    replacements.append({
        "source_object": source_name,
        "actor": actor.get_actor_label(),
        "old_mesh": old_mesh.get_path_name(),
        "new_mesh": new_mesh.get_path_name(),
        "old_size_cm": old_size,
        "new_size_cm": new_size,
        "material_slot_count": len(old_materials),
    })

failures = []
if bounds_mismatches:
    failures.append(f"local bounds mismatches: {len(bounds_mismatches)}")
if slot_mismatches:
    failures.append(f"material slot mismatches: {len(slot_mismatches)}")
if len(replacements) != 336:
    failures.append(f"expected 336 safe replacements, completed {len(replacements)}")

contracts_after = {name: actor_contract(actor) for name, actor in by_source.items()}
# Candidate provenance tags are the only authorised contract delta.
for contract in contracts_after.values():
    contract["tags"] = [
        value for value in contract["tags"]
        if value not in ("LB.PressTrain.Fabrication.v031", "LB.Asset.Candidate.v031")
    ]
for contract in contracts_before.values():
    contract["tags"] = [value for value in contract["tags"] if value != "LB.Asset.CandidateNotPromoted"]
for contract in contracts_after.values():
    # The parent already carried CandidateNotPromoted; collapse duplicates.
    seen = []
    for value in contract["tags"]:
        if value not in seen:
            seen.append(value)
    contract["tags"] = [value for value in seen if value != "LB.Asset.CandidateNotPromoted"]
if contracts_before != contracts_after:
    failures.append("actor transform/hierarchy/collision/navigation/mobility/tag contract changed")

station_count = sum(actor.get_class().get_name() == "LBPressTrainAStation" for actor in actors)
hmi_count = sum(
    isinstance(actor, unreal.TextRenderActor)
    and "LB.HMI.PressTrain.LiveState" in {str(value) for value in actor.tags}
    for actor in actors
)
if station_count != 1:
    failures.append(f"native station count {station_count}, expected 1")
if hmi_count != 1:
    failures.append(f"live HMI count {hmi_count}, expected 1")
if not levels.save_current_level():
    failures.append("could not save v031 map")
base_hash_after = sha256(BASE_FILE)
if base_hash_before != base_hash_after:
    failures.append("protected v027 runtime parent changed")

payload = {
    "$schema": "cairnwell/audit/press-train-a-fabrication-build-v031/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__V013_GEOMETRY_IN_FRESH_V027_RUNTIME_CHILD__LIVE_VISUAL_AND_RUNTIME_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__V031_NOT_A_PARENT",
    "base": BASE,
    "map": MAP,
    "base_sha256_before": base_hash_before,
    "base_sha256_after": base_hash_after,
    "map_sha256": sha256(MAP_FILE) if MAP_FILE.exists() else None,
    "import_destination": DEST,
    "imported_mesh_count": len(imported),
    "presentation_actor_count": len(static_actors),
    "replacement_count": len(replacements),
    "native_station_count": station_count,
    "live_hmi_count": hmi_count,
    "max_sorted_local_bounds_error_cm": max_sorted_bounds_error_cm,
    "bounds_mismatches": bounds_mismatches,
    "material_slot_mismatches": slot_mismatches,
    "actor_contract_unchanged_except_mesh_and_candidate_provenance": contracts_before == contracts_after,
    "replacements": replacements,
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({key: payload[key] for key in (
    "status", "map", "map_sha256", "imported_mesh_count", "replacement_count",
    "native_station_count", "live_hmi_count", "max_sorted_local_bounds_error_cm", "failures"
)}, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
unreal.log("LINE_BOSS_PRESS_TRAIN_A_FABRICATION_V031_BUILD_PASS")
unreal.SystemLibrary.quit_editor()
