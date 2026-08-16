"""Import the visual-only 30 t hoist and bind it in isolated v109."""

from pathlib import Path
from datetime import datetime, timezone
import json
import unreal

MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004SupportHoistCandidate_v109"
DEST = "/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/SupportHoist/Candidate_v001"
NAME = "SM_LB_Crane_SupportHoist_30T_Candidate_v001"
ASSET = f"{DEST}/{NAME}"
ROOT = Path(unreal.Paths.project_dir())
FBX = ROOT / "SourceAssets/IndustrialKit/BridgeCrane/SupportHoist/Candidate_v001/SM_LB_Crane_SupportHoist_30T_Candidate_v001.fbx"
MANIFEST = ROOT / "SourceAssets/IndustrialKit/BridgeCrane/SupportHoist/Candidate_v001/LB_Crane_SupportHoist_30T_Candidate_v001_manifest.json"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr004_support_hoist_candidate_v109.json"
PREFIX = "LB_PR004_V109_"

lib = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

source = json.loads(MANIFEST.read_text(encoding="utf-8"))
if source.get("promotion_authorized") is not False or source.get("authority") != "NONE_VISUAL_ONLY":
    raise RuntimeError("Support-hoist source quarantine contract failed")
if not FBX.is_file() or "ONEDRIVE" in str(FBX).upper():
    raise RuntimeError(f"Invalid canonical FBX: {FBX}")
if not lib.does_asset_exist(MAP):
    raise RuntimeError("Prepared v109 map is missing")

unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX 0")
task = unreal.AssetImportTask()
task.set_editor_properties({
    "filename": str(FBX), "destination_path": DEST, "destination_name": NAME,
    "automated": True, "replace_existing": True, "replace_existing_settings": True,
    "save": True
})
options = unreal.FbxImportUI()
options.set_editor_properties({
    "import_mesh": True, "import_as_skeletal": False,
    "import_materials": False, "import_textures": False,
    "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH
})
options.static_mesh_import_data.set_editor_properties({
    "combine_meshes": True, "generate_lightmap_u_vs": True,
    "auto_generate_collision": False, "import_uniform_scale": 100.0,
    "remove_degenerates": True
})
task.options = options
tools.import_asset_tasks([task])
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
mesh = lib.load_asset(ASSET)
if not isinstance(mesh, unreal.StaticMesh):
    raise RuntimeError(f"Import failed: {ASSET}")
bounds = mesh.get_bounds().box_extent * 2.0
if not (119.0 <= bounds.x <= 123.0 and 91.0 <= bounds.y <= 95.0 and 119.0 <= bounds.z <= 123.0):
    raise RuntimeError(f"Support-hoist bounds failed: {[bounds.x, bounds.y, bounds.z]}")

controlled = {
    "CA_MW_Hoist_LayeredCharcoal": "/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/Candidate_v031/MI_LB_Crane_DarkSteel_v031",
    "CA_MW_Hoist_WorkedSteel": "/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/Candidate_v031/MI_LB_Crane_ExposedSteel_v031",
    "CA_MW_Hoist_SafetyYellow": "/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/Candidate_v031/MI_LB_Crane_RAL1023_Aged_v031",
    "CA_MW_Hoist_RestrainedGreen": "/Game/LineBoss/Robots/Shared/Materials/Candidate_v004/MI_LB_Robot_CairnwellGreen_Restored_v004",
    "CA_MW_Hoist_DarkRubber": "/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/Candidate_v031/MI_LB_Crane_GreaseResidue_v031",
    "CA_MW_Hoist_IdentityIvory": "/Game/LineBoss/IndustrialKit/MaterialHandling/MasterCoil/Candidate_v029/MI_LB_MasterCoil_LabelPaper_v029"
}
loaded = {name: lib.load_asset(path) for name, path in controlled.items()}
if any(value is None for value in loaded.values()):
    raise RuntimeError(f"Missing controlled material: {[k for k,v in loaded.items() if v is None]}")
slot_rows = []
for index, slot in enumerate(mesh.get_editor_property("static_materials")):
    slot_name = str(slot.get_editor_property("material_slot_name"))
    material = next((value for token, value in loaded.items() if token in slot_name), None)
    if material is None:
        raise RuntimeError(f"Unmapped semantic material slot: {slot_name}")
    mesh.set_material(index, material)
    slot_rows.append({"index": index, "slot": slot_name, "material": material.get_path_name()})
lib.save_loaded_asset(mesh, only_if_is_dirty=False)

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
for actor in list(actors.get_all_level_actors()):
    if actor.get_actor_label().startswith(PREFIX):
        actors.destroy_actor(actor)

hoist = next((actor for actor in actors.get_all_level_actors()
              if actor.get_actor_label() == "LB_INT_FRONT_30T_HoistBlock"), None)
if hoist is None:
    raise RuntimeError("Missing inherited 30 t upper-hoist actor")
component = hoist.get_component_by_class(unreal.StaticMeshComponent)
if component is None:
    raise RuntimeError("Inherited 30 t hoist has no static-mesh component")
previous_mesh = component.get_editor_property("static_mesh")
previous_path = previous_mesh.get_path_name() if previous_mesh else None
component.set_static_mesh(mesh)
component.set_mobility(unreal.ComponentMobility.MOVABLE)
component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
component.set_collision_profile_name(unreal.Name("NoCollision"))
component.set_editor_property("can_ever_affect_navigation", False)
hoist.tags = list(hoist.tags) + [unreal.Name("LB.Module.SupportHoistPurposeBuilt"),
                                 unreal.Name("LB.Identity.CR-30-01"),
                                 unreal.Name("LB.Asset.Candidate.v109"),
                                 unreal.Name("LB.Asset.CandidateNotPromoted")]

def camera(label, location, target, fov, bias):
    actor = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(PREFIX + "CAM_" + label)
    actor.tags = [unreal.Name("LB.Camera.Validation"), unreal.Name("LB.Camera.Fixed.SupportHoist.v109"),
                  unreal.Name("LB.Asset.Candidate.v109"), unreal.Name("LB.Asset.CandidateNotPromoted")]
    actor.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(actor.get_actor_location(), unreal.Vector(*target)), False)
    actor.camera_component.set_editor_properties({"field_of_view": fov, "aspect_ratio": 16.0/9.0,
        "constrain_aspect_ratio": True, "post_process_blend_weight": 1.0})
    settings = actor.camera_component.get_editor_property("post_process_settings")
    settings.set_editor_properties({"override_auto_exposure_method": True,
        "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
        "override_auto_exposure_min_brightness": True, "override_auto_exposure_max_brightness": True,
        "auto_exposure_min_brightness": 1.0, "auto_exposure_max_brightness": 1.0,
        "override_auto_exposure_bias": True, "auto_exposure_bias": bias})
    actor.camera_component.set_editor_property("post_process_settings", settings)
    return actor

cameras = [
    camera("SupportHoistParkClose", (-8520.0, -3920.0, 1260.0), (-9100.0, -4700.0, 1120.0), 43.0, 0.08),
    camera("SupportHoistOnStationClose", (-7100.0, -3900.0, 1120.0), (-7600.0, -4700.0, 900.0), 45.0, 0.08),
    camera("SupportFleetIdentity", (-6900.0, 260.0, 980.0), (-8500.0, -3800.0, 1300.0), 55.0, 0.02)
]

if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")

payload = {
    "$schema": "cairnwell/audit/press-shop-pr004-support-hoist-candidate-v109/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "SOURCE_AND_UNREAL_IMPORT_PASS__RUNTIME_COLLISION_NAVIGATION_SAVE_AUTHORITY_AND_FRESH_VISUAL_REGATES_REQUIRED__NOT_PROMOTED",
    "base_map": "/Game/LineBoss/Maps/LB_PressShop_PR004PackageConditionCandidate_v108",
    "map": MAP, "asset": mesh.get_path_name(),
    "bounds_cm": [bounds.x, bounds.y, bounds.z],
    "semantic_material_slots": slot_rows,
    "replaced_actor": hoist.get_actor_label(), "previous_mesh": previous_path,
    "moving_tags_preserved": [str(tag) for tag in hoist.tags if str(tag).startswith("LB.Motion") or str(tag) == "LB.Crane.30T"],
    "fixed_cameras": [actor.get_actor_label() for actor in cameras],
    "authority_changed": False, "production_map_changed": False,
    "promotion_authorized": False
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"CAIRNWELL_PR004_SUPPORT_HOIST_V109_BUILD_PASS bounds={[bounds.x,bounds.y,bounds.z]}")
unreal.SystemLibrary.quit_editor()
