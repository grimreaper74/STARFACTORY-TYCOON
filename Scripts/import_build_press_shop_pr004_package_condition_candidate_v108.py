"""Import master coil v005 and build an isolated PR-004 package-condition successor.

The map is duplicated from the proven v042 PR-004/PR-005 handoff checkpoint.
Only packaged-coil render meshes and one fixed evidence camera change. Native
station, crane, traceability, material-flow and save authority are preserved.
"""

from datetime import datetime, timezone
from pathlib import Path
import json

import unreal


BASE = "/Game/LineBoss/Maps/LB_PressShop_PR004PR005HandoffCandidate_v042"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004PackageConditionCandidate_v108"
DEST = "/Game/LineBoss/IndustrialKit/MaterialHandling/MasterCoil/Candidate_v005"
NAME = "SM_LB_MasterCoil_Candidate_v005"
MESH_PATH = f"{DEST}/{NAME}"
OLD_MESH_PATH = "/Game/LineBoss/IndustrialKit/MaterialHandling/MasterCoil/Candidate_v029/ReleaseScale_v002/SM_LB_MasterCoil_Candidate_v004"
ROOT = Path(unreal.Paths.project_dir())
FBX = ROOT / "SourceAssets/IndustrialKit/MasterCoil/Candidate_v005/SM_LB_MasterCoil_Candidate_v005.fbx"
MANIFEST = ROOT / "SourceAssets/IndustrialKit/MasterCoil/Candidate_v005/master_coil_candidate_v005_manifest.json"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr004_package_condition_candidate_v108.json"
PREFIX = "LB_PR004_V108_"

lib = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def collision_counts(static_mesh):
    setup = static_mesh.get_editor_property("body_setup") if isinstance(static_mesh, unreal.StaticMesh) else None
    aggregate = setup.get_editor_property("agg_geom") if setup else None
    if aggregate is None:
        return {"box": 0, "sphere": 0, "capsule": 0, "convex": 0, "total": 0}
    result = {
        "box": len(aggregate.get_editor_property("box_elems")),
        "sphere": len(aggregate.get_editor_property("sphere_elems")),
        "capsule": len(aggregate.get_editor_property("sphyl_elems")),
        "convex": len(aggregate.get_editor_property("convex_elems")),
    }
    result["total"] = sum(result.values())
    return result


source = json.loads(MANIFEST.read_text(encoding="utf-8"))
if source.get("promotion_authorized") is not False or source.get("collision", {}).get("count") != 12:
    raise RuntimeError("Master coil v005 source quarantine/collision contract failed")
if not FBX.is_file() or "ONEDRIVE" in str(FBX).upper():
    raise RuntimeError(f"Invalid canonical source FBX {FBX}")

# Preserve authored UCX through the legacy FBX static-mesh factory. The exact
# post-import primitive and bounds gates below reject fallback collision.
unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX 0")
task = unreal.AssetImportTask()
task.set_editor_properties({
    "filename": str(FBX),
    "destination_path": DEST,
    "destination_name": NAME,
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
static_data = options.get_editor_property("static_mesh_import_data")
static_data.set_editor_properties({
    "combine_meshes": True,
    "convert_scene": True,
    "convert_scene_unit": True,
    "force_front_x_axis": False,
    "generate_lightmap_u_vs": True,
    "auto_generate_collision": True,
    "remove_degenerates": True,
    "one_convex_hull_per_ucx": True,
    "import_uniform_scale": 1.0,
})
task.set_editor_property("options", options)
tools.import_asset_tasks([task])
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

mesh = lib.load_asset(MESH_PATH)
old_mesh = lib.load_asset(OLD_MESH_PATH)
if not isinstance(mesh, unreal.StaticMesh) or not isinstance(old_mesh, unreal.StaticMesh):
    raise RuntimeError("New or proven packaged-coil mesh could not be loaded")

counts = collision_counts(mesh)
if counts["total"] != 12 or counts["convex"] != 12:
    raise RuntimeError(f"Expected twelve authored convex hulls, found {counts}")
body = mesh.get_editor_property("body_setup")
body.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_DEFAULT)
body.modify()

box = mesh.get_bounding_box()
bounds_cm = [box.max.x - box.min.x, box.max.y - box.min.y, box.max.z - box.min.z]
if not (149.9 <= bounds_cm[0] <= 150.2 and 189.9 <= bounds_cm[1] <= 190.2
        and 189.9 <= bounds_cm[2] <= 190.2):
    raise RuntimeError(f"Master coil v005 Unreal bounds failed: {bounds_cm}")

new_slots = mesh.get_editor_property("static_materials")
old_slots = old_mesh.get_editor_property("static_materials")
if len(new_slots) != 10 or len(old_slots) != 10:
    raise RuntimeError(f"Semantic slot parity failed new={len(new_slots)} old={len(old_slots)}")
slot_rows = []
for index, slot in enumerate(new_slots):
    new_name = str(slot.get_editor_property("imported_material_slot_name")
                   or slot.get_editor_property("material_slot_name"))
    old_slot = old_slots[index]
    old_name = str(old_slot.get_editor_property("imported_material_slot_name")
                   or old_slot.get_editor_property("material_slot_name"))
    material = old_mesh.get_material(index)
    if new_name != old_name or material is None:
        raise RuntimeError(f"Material slot parity failed at {index}: {new_name} / {old_name}")
    mesh.set_material(index, material)
    slot_rows.append({"index": index, "slot": new_name, "material": material.get_path_name()})
mesh.modify()
lib.save_loaded_asset(mesh, only_if_is_dirty=False)

if not lib.does_asset_exist(MAP):
    raise RuntimeError(
        f"Prepared map is missing: {MAP}. Run the v108 prepare script in a separate UE process first."
    )
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

for actor in list(actors.get_all_level_actors()):
    if actor.get_actor_label().startswith(PREFIX):
        actors.destroy_actor(actor)

replaced = []
station_present = False
for actor in actors.get_all_level_actors():
    for component in actor.get_components_by_class(unreal.StaticMeshComponent):
        current = component.get_editor_property("static_mesh")
        current_path = current.get_path_name() if current else ""
        if "SM_LB_MasterCoil_Candidate_v004" not in current_path and NAME not in current_path:
            continue
        component.set_static_mesh(mesh)
        component.set_editor_property("can_ever_affect_navigation", False)
        component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
        component.set_collision_profile_name(unreal.Name("BlockAll"))
        actor.tags = list(actor.tags) + [unreal.Name("LB.Asset.Candidate.v108"),
                                         unreal.Name("LB.Material.PackagedCoil.Condition.v005")]
        replaced.append({"actor": actor.get_actor_label(), "component": component.get_name()})
        if component.get_name() == "PR004_WrappedCoilVisual":
            station_present = True

if len(replaced) != 15 or not station_present:
    raise RuntimeError(f"Expected 15 packaged presentations including native PR-004, got {replaced}")

camera = actors.spawn_actor_from_class(
    unreal.CameraActor, unreal.Vector(-4520.0, -1370.0, 330.0), unreal.Rotator())
camera.set_actor_label(PREFIX + "CAM_PackageConditionClose")
camera.tags = [unreal.Name("LB.Camera.Validation"), unreal.Name("LB.Camera.Fixed.PR004Package.v108"),
               unreal.Name("LB.Asset.Candidate.v108"), unreal.Name("LB.Asset.CandidateNotPromoted")]
camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
    camera.get_actor_location(), unreal.Vector(-5050.0, -1925.0, 145.0)), False)
camera.camera_component.set_editor_properties({
    "field_of_view": 39.0,
    "aspect_ratio": 16.0 / 9.0,
    "constrain_aspect_ratio": True,
    "post_process_blend_weight": 1.0,
})
settings = camera.camera_component.get_editor_property("post_process_settings")
settings.set_editor_properties({
    "override_auto_exposure_method": True,
    "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
    "override_auto_exposure_min_brightness": True,
    "override_auto_exposure_max_brightness": True,
    "auto_exposure_min_brightness": 1.0,
    "auto_exposure_max_brightness": 1.0,
    "override_auto_exposure_bias": True,
    "auto_exposure_bias": -0.02,
})
camera.camera_component.set_editor_property("post_process_settings", settings)

if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")

payload = {
    "$schema": "cairnwell/audit/press-shop-pr004-package-condition-candidate-v108/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "SOURCE_AND_UNREAL_IMPORT_PASS__RUNTIME_COLLISION_NAVIGATION_SAVE_AUTHORITY_AND_FRESH_VISUAL_REGATES_REQUIRED__NOT_PROMOTED",
    "base_map": BASE,
    "map": MAP,
    "asset": mesh.get_path_name(),
    "source_manifest": str(MANIFEST),
    "source_hashes": source.get("hashes"),
    "bounds_cm": bounds_cm,
    "collision": counts,
    "collision_trace_flag": str(body.get_editor_property("collision_trace_flag")),
    "semantic_material_slots": slot_rows,
    "packaged_component_count": len(replaced),
    "native_station_component_present": station_present,
    "replaced_components": replaced,
    "fixed_camera": camera.get_actor_label(),
    "authority_changed": False,
    "production_map_changed": False,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"CAIRNWELL_PR004_PACKAGE_CONDITION_V108_BUILD_PASS replacements={len(replaced)} bounds_cm={bounds_cm} ucx={counts['total']}")
unreal.SystemLibrary.quit_editor()
