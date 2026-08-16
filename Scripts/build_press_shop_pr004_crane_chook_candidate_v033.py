"""Import and bind the dimensioned v033 C-hook in an isolated Unreal map."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004CraneCHookCandidate_v033"
DEST = "/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/CHook/Candidate_v033"
ASSET = DEST + "/SM_LB_Crane_CHook_Candidate_v033"
FBX = Path(unreal.Paths.project_dir()) / "SourceAssets/IndustrialKit/BridgeCrane/CHook/Candidate_v033/SM_LB_Crane_CHook_Candidate_v033.fbx"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr004_crane_chook_candidate_v033.json"
PREFIX = "LB_PR004_V033_"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
library = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
if "ONEDRIVE" in str(FBX).upper() or not FBX.is_file():
    raise RuntimeError(f"Invalid canonical FBX source: {FBX}")
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
for actor in list(actors.get_all_level_actors()):
    if actor.get_actor_label().startswith(PREFIX):
        actors.destroy_actor(actor)

unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX 0")
if library.does_asset_exist(ASSET):
    library.delete_asset(ASSET)
task = unreal.AssetImportTask()
task.set_editor_properties({"filename": str(FBX), "destination_path": DEST,
                            "destination_name": "SM_LB_Crane_CHook_Candidate_v033",
                            "automated": True, "replace_existing": True, "save": True})
options = unreal.FbxImportUI()
options.set_editor_properties({"import_mesh": True, "import_materials": False,
                               "import_textures": False,
                               "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
                               "automated_import_should_detect_type": False})
options.static_mesh_import_data.set_editor_properties({"combine_meshes": True,
                                                        "generate_lightmap_u_vs": True,
                                                        "auto_generate_collision": True,
                                                        "import_uniform_scale": 100.0})
task.options = options
tools.import_asset_tasks([task])
mesh = library.load_asset(ASSET)
if mesh is None:
    raise RuntimeError(f"Failed to import {ASSET}")
bounds = mesh.get_bounds().box_extent * 2.0
if not (235.0 <= bounds.x <= 248.0 and 50.0 <= bounds.y <= 62.0 and 195.0 <= bounds.z <= 208.0):
    raise RuntimeError(f"Purpose-built hook import bounds out of gate: {[bounds.x, bounds.y, bounds.z]}")

yellow = library.load_asset("/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/Candidate_v031/MI_LB_Crane_RAL1023_Aged_v031")
dark = library.load_asset("/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/Candidate_v031/MI_LB_Crane_DarkSteel_v031")
steel = library.load_asset("/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/Candidate_v031/MI_LB_Crane_ExposedSteel_v031")
rubber = library.load_asset("/Game/LineBoss/Stations/Press/PR005/Candidate_v001/Materials/M_PR005_Rubber")
if any(value is None for value in (yellow, dark, steel, rubber)):
    raise RuntimeError("Missing controlled hook materials")
slot_materials = {"LB_Crane_RAL1023_Aged": yellow, "LB_Crane_DarkSteel": dark,
                  "LB_Crane_ExposedSteel": steel, "LB_Crane_BorePad": rubber}
for index, slot in enumerate(mesh.get_editor_property("static_materials")):
    imported_name = str(slot.get_editor_property("material_slot_name"))
    for token, material in slot_materials.items():
        if token in imported_name:
            mesh.set_material(index, material)
            break
library.save_loaded_asset(mesh, only_if_is_dirty=False)

old_hook = next((actor for actor in actors.get_all_level_actors()
                 if actor.get_actor_label() == "LB_INT_FRONT_40T_CHook"), None)
if old_hook is None:
    raise RuntimeError("Missing inherited 40 t hook")
old_hook.set_is_temporarily_hidden_in_editor(True)
old_hook.set_actor_hidden_in_game(True)
old_hook.tags = [tag for tag in old_hook.tags if str(tag) not in
                 {"LB.Motion.CHook", "LB.Animation.Pivot.CHook"}]

hook = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(-5050.0, -2150.0, 820.0), unreal.Rotator(yaw=90.0))
hook.set_actor_label(PREFIX + "40T_CHook_PurposeBuilt")
hook.tags = [unreal.Name(value) for value in (
    "LB.Motion.CHook", "LB.Crane.40T", "LB.Safety.Padded", "LB.Animation.Pivot.CHook",
    "LB.Module.CHookPurposeBuilt", "LB.Asset.Candidate.v033", "LB.Asset.CandidateNotPromoted")]
hook.static_mesh_component.set_static_mesh(mesh)
hook.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE)
hook.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
hook.static_mesh_component.set_collision_profile_name(unreal.Name("NoCollision"))
hook.static_mesh_component.set_editor_property("can_ever_affect_navigation", False)

# Moderately recover mid-level visibility without the v032 hot ceiling/task wash.
light_changes = []
for actor in actors.get_all_level_actors():
    label = actor.get_actor_label()
    light = actor.get_component_by_class(unreal.LightComponent)
    if light is None or not label.startswith("LB_INT_FRONT_FactoryFill_"):
        continue
    old = float(light.get_editor_property("intensity"))
    number = int(label.rsplit("_", 1)[-1])
    new = 620.0 if number in (10, 11, 12) else 440.0
    light.set_editor_property("intensity", new)
    light_changes.append({"actor": label, "old": old, "new": new})

def camera(label, location, target, fov, bias):
    actor = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(PREFIX + "CAM_" + label)
    actor.tags = [unreal.Name(value) for value in ("LB.Camera.Validation", "LB.Camera.Fixed.PR004Crane.v033",
                                                   "LB.Asset.Candidate.v033", "LB.Asset.CandidateNotPromoted")]
    actor.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(actor.get_actor_location(), unreal.Vector(*target)), False)
    component = actor.camera_component
    component.set_editor_properties({"field_of_view": fov, "aspect_ratio": 16.0/9.0,
                                     "constrain_aspect_ratio": True, "post_process_blend_weight": 1.0})
    settings = component.get_editor_property("post_process_settings")
    settings.set_editor_properties({"override_auto_exposure_method": True,
        "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
        "override_auto_exposure_min_brightness": True, "override_auto_exposure_max_brightness": True,
        "auto_exposure_min_brightness": 1.0, "auto_exposure_max_brightness": 1.0,
        "override_auto_exposure_bias": True, "auto_exposure_bias": bias})
    component.set_editor_property("post_process_settings", settings)
    return actor

cameras = [
    camera("CraneFullSpanWest", (-10150.0, -1500.0, 1120.0), (-5050.0, -2415.0, 1460.0), 73.0, -0.35),
    camera("CHookPurposeBuilt", (-6000.0, -900.0, 980.0), (-5050.0, -1850.0, 780.0), 37.0, -0.05),
    camera("PR004Deposit", (-5850.0, -330.0, 720.0), (-5050.0, -2000.0, 180.0), 44.0, -0.25),
]
if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")
payload = {"$schema": "line-boss/audit/press-shop-pr004-crane-chook-candidate-v033/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PURPOSE_BUILT_CHOOK_IMPORTED_AND_BOUND__REGATES_REQUIRED__NOT_PROMOTED",
    "map": MAP, "source_fbx": str(FBX), "asset": ASSET,
    "mesh_bounds_cm": [bounds.x, bounds.y, bounds.z], "hook_actor": hook.get_actor_label(),
    "hook_datum_z_cm": 820.0, "hook_yaw_deg": 90.0,
    "bore_axis_world": "Y", "body_to_load_centre_y_cm": 150.0,
    "bore_arm_centre_below_datum_cm": 59.0,
    "old_hook_hidden_and_unbound": True, "light_changes": light_changes,
    "fixed_cameras": [actor.get_actor_label() for actor in cameras],
    "bridge_span_cm_unchanged": 6210.0, "promotion_authorized": False}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR004_CRANE_V033_BUILD_PASS bounds={payload['mesh_bounds_cm']} map={MAP}")
unreal.SystemLibrary.quit_editor()
