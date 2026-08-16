"""Import and bind the general-purpose CR-30-01 maintenance hook block."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004SupportHookCandidate_v037"
DEST = "/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/SupportHook/Candidate_v037"
ASSET = DEST + "/SM_LB_Crane_SupportHookBlock_30T_Candidate_v037"
FBX = Path(unreal.Paths.project_dir()) / (
    "SourceAssets/IndustrialKit/BridgeCrane/SupportHook/Candidate_v037/"
    "SM_LB_Crane_SupportHookBlock_30T_Candidate_v037.fbx")
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr004_support_hook_candidate_v037.json"
PREFIX = "LB_PR004_V037_"
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
    "destination_name": "SM_LB_Crane_SupportHookBlock_30T_Candidate_v037",
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
    raise RuntimeError(f"Support hook bounds out of gate: {[bounds.x, bounds.y, bounds.z]}")

yellow = library.load_asset(
    "/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/Candidate_v031/MI_LB_Crane_RAL1023_Aged_v031")
dark = library.load_asset(
    "/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/Candidate_v031/MI_LB_Crane_DarkSteel_v031")
steel = library.load_asset(
    "/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/Candidate_v031/MI_LB_Crane_ExposedSteel_v031")
red = library.load_asset("/Game/LineBoss/Stations/Press/PR005/Candidate_v001/Materials/M_PR005_SafetyRed")
if any(value is None for value in (yellow, dark, steel, red)):
    raise RuntimeError("Missing controlled support-hook materials")
slot_materials = {
    "LB_Crane_RAL1023_Aged": yellow,
    "LB_Crane_DarkSteel": dark,
    "LB_Crane_ExposedSteel": steel,
    "LB_Crane_SafetyLatch": red,
}
for index, slot in enumerate(mesh.get_editor_property("static_materials")):
    imported_name = str(slot.get_editor_property("material_slot_name"))
    for token, material in slot_materials.items():
        if token in imported_name:
            mesh.set_material(index, material)
            break
library.save_loaded_asset(mesh, only_if_is_dirty=False)

old_hook = next((actor for actor in actors.get_all_level_actors()
                 if actor.get_actor_label() == "LB_INT_FRONT_30T_CHook"), None)
if old_hook is None:
    raise RuntimeError("Missing inherited 30 t C-hook")
old_hook.set_is_temporarily_hidden_in_editor(True)
old_hook.set_actor_hidden_in_game(True)
old_hook.tags = [tag for tag in old_hook.tags if str(tag) not in {
    "LB.Motion.CHook", "LB.Animation.Pivot.CHook", "LB.Crane.30T"}]

hook = actors.spawn_actor_from_class(
    unreal.StaticMeshActor, unreal.Vector(-9100.0, -4700.0, 1010.0), unreal.Rotator())
hook.set_actor_label(PREFIX + "30T_SupportHookBlock_PurposeBuilt")
hook.tags = names(
    "LB.Motion.CHook", "LB.Crane.30T", "LB.Animation.Pivot.CHook",
    "LB.Module.SupportHookPurposeBuilt", "LB.Operations.MaintenanceOnly",
    "LB.Asset.Candidate.v037", "LB.Asset.CandidateNotPromoted")
hook.static_mesh_component.set_static_mesh(mesh)
hook.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE)
hook.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
hook.static_mesh_component.set_collision_profile_name(unreal.Name("NoCollision"))
hook.static_mesh_component.set_editor_property("can_ever_affect_navigation", False)


def cube(label, location, dimensions, material, actor_tags):
    actor = actors.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(PREFIX + label)
    actor.tags = names(*actor_tags, "LB.Asset.Candidate.v037", "LB.Asset.CandidateNotPromoted")
    actor.static_mesh_component.set_static_mesh(library.load_asset("/Engine/BasicShapes/Cube"))
    actor.set_actor_scale3d(unreal.Vector(
        dimensions[0] / 100.0, dimensions[1] / 100.0, dimensions[2] / 100.0))
    actor.static_mesh_component.set_material(0, material)
    actor.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    actor.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    actor.static_mesh_component.set_editor_property("can_ever_affect_navigation", False)
    return actor


# Camera-facing bridge identity follows bridge X but not trolley travel.
identity_tags = ("LB.Motion.CraneBridge", "LB.Crane.30T", "LB.Module.CraneIdentity")
identity_backing = cube(
    "30T_EastIdentity_Back", (-9024.0, -3300.0, 1505.0), (5.0, 330.0, 72.0), dark, identity_tags)
identity_text = actors.spawn_actor_from_class(
    unreal.TextRenderActor, unreal.Vector(-9019.0, -3300.0, 1505.0), unreal.Rotator())
identity_text.set_actor_label(PREFIX + "30T_EastIdentity_Text")
identity_text.tags = names(*identity_tags, "LB.Asset.Candidate.v037", "LB.Asset.CandidateNotPromoted")
identity_text.text_render.set_editor_properties({
    "text": "CAIRNWELL AUTOMOTIVE\nCR-30-01  |  SWL 30 t  |  SUPPORT",
    "world_size": 17.0,
    "horizontal_alignment": unreal.HorizTextAligment.EHTA_CENTER,
    "vertical_alignment": unreal.VerticalTextAligment.EVRTA_TEXT_CENTER,
    "text_render_color": unreal.Color(232, 236, 226, 255),
    "can_ever_affect_navigation": False,
    "mobility": unreal.ComponentMobility.MOVABLE,
})
identity_text.text_render.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)


def spot(label, location, target, intensity, radius):
    light = actors.spawn_actor_from_class(
        unreal.SpotLight, unreal.Vector(*location), unreal.Rotator())
    light.set_actor_label(PREFIX + label)
    light.tags = names(
        "LB.Lighting.Candidate", "LB.Lighting.SupportCraneTask",
        "LB.Asset.Candidate.v037", "LB.Asset.CandidateNotPromoted")
    light.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
        light.get_actor_location(), unreal.Vector(*target)), False)
    light.spot_light_component.set_editor_properties({
        "intensity": intensity, "attenuation_radius": radius,
        "inner_cone_angle": 28.0, "outer_cone_angle": 58.0,
        "source_radius": 70.0, "soft_source_radius": 140.0,
        "cast_shadows": False, "light_color": unreal.Color(226, 235, 246, 255),
    })
    return light


lights = [
    spot("SupportParkTask", (-7900.0, -3600.0, 1500.0),
         (-9100.0, -4700.0, 1080.0), 650.0, 2500.0),
    spot("SupportServiceTask", (-6800.0, -2200.0, 1450.0),
         (-7600.0, -3300.0, 930.0), 760.0, 2400.0),
]


def camera(label, location, target, fov, bias):
    actor = actors.spawn_actor_from_class(
        unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(PREFIX + "CAM_" + label)
    actor.tags = names(
        "LB.Camera.Validation", "LB.Camera.Fixed.SupportCrane.v037",
        "LB.Asset.Candidate.v037", "LB.Asset.CandidateNotPromoted")
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
    camera("SupportOnStationIdentity", (-6400.0, -1000.0, 980.0),
           (-7600.0, -3300.0, 1120.0), 48.0, 0.06),
    camera("SupportHookClose", (-6900.0, -2450.0, 1050.0),
           (-7600.0, -3300.0, 760.0), 36.0, 0.10),
]

if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")
payload = {
    "$schema": "line-boss/audit/press-shop-pr004-support-hook-candidate-v037/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "GENERAL_PURPOSE_SUPPORT_HOOK_IMPORTED_AND_BOUND__REGATES_REQUIRED__NOT_PROMOTED",
    "base_map": "/Game/LineBoss/Maps/LB_PressShop_PR004SupportCraneCandidate_v036",
    "map": MAP, "source_fbx": str(FBX), "asset": ASSET,
    "mesh_bounds_cm": [bounds.x, bounds.y, bounds.z],
    "rated_load_t": 30.0, "role": "general-purpose maintenance support",
    "master_coil_authority": False,
    "old_c_hook_hidden_and_unbound": True,
    "hook_actor": hook.get_actor_label(), "hook_datum_z_cm": 1010.0,
    "identity_actors": [identity_backing.get_actor_label(), identity_text.get_actor_label()],
    "task_lights": [light.get_actor_label() for light in lights],
    "fixed_cameras": [camera.get_actor_label() for camera in cameras],
    "v036_native_controller_and_interlocks_retained": True,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR004_SUPPORT_HOOK_V037_BUILD_PASS bounds={payload['mesh_bounds_cm']} map={MAP}")
unreal.SystemLibrary.quit_editor()
