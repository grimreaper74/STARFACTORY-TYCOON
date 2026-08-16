"""Bind guarded support hook and move maintenance service clear of coil inventory."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004SupportHookCandidate_v038"
DEST = "/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/SupportHook/Candidate_v038"
ASSET = DEST + "/SM_LB_Crane_SupportHookBlock_30T_Candidate_v038"
FBX = Path(unreal.Paths.project_dir()) / (
    "SourceAssets/IndustrialKit/BridgeCrane/SupportHook/Candidate_v038/"
    "SM_LB_Crane_SupportHookBlock_30T_Candidate_v038.fbx")
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr004_support_hook_candidate_v038.json"
PREFIX = "LB_PR004_V038_"
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


def names(*values):
    return [unreal.Name(value) for value in values]


unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX 0")
if library.does_asset_exist(ASSET):
    library.delete_asset(ASSET)
task = unreal.AssetImportTask()
task.set_editor_properties({
    "filename": str(FBX), "destination_path": DEST,
    "destination_name": "SM_LB_Crane_SupportHookBlock_30T_Candidate_v038",
    "automated": True, "replace_existing": True, "save": True,
})
options = unreal.FbxImportUI()
options.set_editor_properties({
    "import_mesh": True, "import_materials": False, "import_textures": False,
    "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
    "automated_import_should_detect_type": False,
})
options.static_mesh_import_data.set_editor_properties({
    "combine_meshes": True, "generate_lightmap_u_vs": True,
    "auto_generate_collision": True, "import_uniform_scale": 100.0,
})
task.options = options
tools.import_asset_tasks([task])
mesh = library.load_asset(ASSET)
if mesh is None:
    raise RuntimeError(f"Failed to import {ASSET}")
bounds = mesh.get_bounds().box_extent * 2.0
if not (114.0 <= bounds.x <= 121.0 and 66.0 <= bounds.y <= 73.0 and 157.0 <= bounds.z <= 165.0):
    raise RuntimeError(f"Guarded hook bounds out of gate: {[bounds.x, bounds.y, bounds.z]}")

controlled = {
    "LB_Crane_RAL1023_Aged": library.load_asset(
        "/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/Candidate_v031/MI_LB_Crane_RAL1023_Aged_v031"),
    "LB_Crane_DarkSteel": library.load_asset(
        "/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/Candidate_v031/MI_LB_Crane_DarkSteel_v031"),
    "LB_Crane_ExposedSteel": library.load_asset(
        "/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/Candidate_v031/MI_LB_Crane_ExposedSteel_v031"),
    "LB_Crane_SafetyLatch": library.load_asset(
        "/Game/LineBoss/Stations/Press/PR005/Candidate_v001/Materials/M_PR005_SafetyRed"),
}
if any(value is None for value in controlled.values()):
    raise RuntimeError("Missing controlled guarded-hook materials")
for index, slot in enumerate(mesh.get_editor_property("static_materials")):
    imported_name = str(slot.get_editor_property("material_slot_name"))
    for token, material in controlled.items():
        if token in imported_name:
            mesh.set_material(index, material)
            break
library.save_loaded_asset(mesh, only_if_is_dirty=False)

old_hook = next((actor for actor in actors.get_all_level_actors()
                 if actor.get_actor_label() == "LB_PR004_V037_30T_SupportHookBlock_PurposeBuilt"), None)
if old_hook is None:
    raise RuntimeError("Missing inherited v037 support hook")
old_hook.set_is_temporarily_hidden_in_editor(True)
old_hook.set_actor_hidden_in_game(True)
old_hook.tags = [tag for tag in old_hook.tags if str(tag) not in {
    "LB.Motion.CHook", "LB.Animation.Pivot.CHook", "LB.Crane.30T"}]

hook = actors.spawn_actor_from_class(
    unreal.StaticMeshActor, unreal.Vector(-9100.0, -4700.0, 1010.0), unreal.Rotator())
hook.set_actor_label(PREFIX + "30T_SupportHookBlock_Guarded")
hook.tags = names(
    "LB.Motion.CHook", "LB.Crane.30T", "LB.Animation.Pivot.CHook",
    "LB.Module.SupportHookPurposeBuilt", "LB.Module.SupportHookSheaveGuard",
    "LB.Operations.MaintenanceOnly", "LB.Asset.Candidate.v038",
    "LB.Asset.CandidateNotPromoted")
hook.static_mesh_component.set_static_mesh(mesh)
hook.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE)
hook.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
hook.static_mesh_component.set_collision_profile_name(unreal.Name("NoCollision"))
hook.static_mesh_component.set_editor_property("can_ever_affect_navigation", False)

service_point = next((actor for actor in actors.get_all_level_actors()
                      if unreal.Name("LB.Crane.SupportPoint.FrontEndMaintenance") in actor.tags), None)
if service_point is None:
    raise RuntimeError("Missing inherited maintenance service point")
service_point.set_actor_location(unreal.Vector(-7600.0, -4700.0, 760.0), False, False)
service_point.tags = list(service_point.tags) + names(
    "LB.ServiceEnvelope.CoilInventoryClear", "LB.Asset.Candidate.v038")

identity_back = next((actor for actor in actors.get_all_level_actors()
                      if actor.get_actor_label() == "LB_PR004_V037_30T_EastIdentity_Back"), None)
identity_text = next((actor for actor in actors.get_all_level_actors()
                      if actor.get_actor_label() == "LB_PR004_V037_30T_EastIdentity_Text"), None)
if identity_back is None or identity_text is None:
    raise RuntimeError("Missing v037 support-crane identity")
back_scale = identity_back.get_actor_scale3d()
identity_back.set_actor_scale3d(unreal.Vector(back_scale.x, back_scale.y * 1.20, back_scale.z * 1.18))
identity_text.text_render.set_world_size(20.0)
identity_text.text_render.set_text("CAIRNWELL AUTOMOTIVE\nCR-30-01  |  SWL 30 t  |  SUPPORT")

service_light = next((actor for actor in actors.get_all_level_actors()
                      if actor.get_actor_label() == "LB_PR004_V037_SupportServiceTask"), None)
if service_light is not None:
    service_light.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
        service_light.get_actor_location(), unreal.Vector(-7600.0, -4700.0, 930.0)), False)


def camera(label, location, target, fov, bias):
    actor = actors.spawn_actor_from_class(
        unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(PREFIX + "CAM_" + label)
    actor.tags = names(
        "LB.Camera.Validation", "LB.Camera.Fixed.SupportCrane.v038",
        "LB.Asset.Candidate.v038", "LB.Asset.CandidateNotPromoted")
    actor.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
        actor.get_actor_location(), unreal.Vector(*target)), False)
    component = actor.camera_component
    component.set_editor_properties({
        "field_of_view": fov, "aspect_ratio": 16.0 / 9.0,
        "constrain_aspect_ratio": True, "post_process_blend_weight": 1.0,
    })
    settings = component.get_editor_property("post_process_settings")
    settings.set_editor_properties({
        "override_auto_exposure_method": True,
        "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
        "override_auto_exposure_min_brightness": True,
        "override_auto_exposure_max_brightness": True,
        "auto_exposure_min_brightness": 1.0,
        "auto_exposure_max_brightness": 1.0,
        "override_auto_exposure_bias": True,
        "auto_exposure_bias": bias,
    })
    component.set_editor_property("post_process_settings", settings)
    return actor


cameras = [
    camera("SupportParkIdentity", (-7350.0, -900.0, 1050.0),
           (-9000.0, -3900.0, 1260.0), 50.0, 0.04),
    camera("SupportOnStationClear", (-6350.0, -2450.0, 1000.0),
           (-7600.0, -4700.0, 1080.0), 48.0, 0.08),
    camera("SupportHookGuardClose", (-6800.0, -3850.0, 1020.0),
           (-7600.0, -4700.0, 760.0), 34.0, 0.12),
]

if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")
payload = {
    "$schema": "line-boss/audit/press-shop-pr004-support-hook-candidate-v038/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "GUARDED_SUPPORT_HOOK_AND_CLEAR_SERVICE_ENVELOPE_BUILT__REGATES_REQUIRED__NOT_PROMOTED",
    "base_map": "/Game/LineBoss/Maps/LB_PressShop_PR004SupportHookCandidate_v037",
    "map": MAP, "source_fbx": str(FBX), "asset": ASSET,
    "mesh_bounds_cm": [bounds.x, bounds.y, bounds.z],
    "rated_load_t": 30.0, "role": "general-purpose maintenance support",
    "master_coil_authority": False, "near_sheave_guard": True,
    "old_v037_hook_hidden_and_unbound": True,
    "service_datums_cm": {"bridge_x": -7600.0, "trolley_y": -4700.0, "hook_z": 760.0},
    "service_envelope": "receiving-side clear maintenance envelope; no coil inventory datum",
    "identity_enlarged": True,
    "fixed_cameras": [camera.get_actor_label() for camera in cameras],
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR004_SUPPORT_HOOK_V038_BUILD_PASS bounds={payload['mesh_bounds_cm']} map={MAP}")
unreal.SystemLibrary.quit_editor()
