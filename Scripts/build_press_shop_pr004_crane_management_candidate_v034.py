"""Author v034 crane hierarchy, floor lighting and packaged-load finish."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004CraneManagementCandidate_v034"
DEST = "/Game/LineBoss/IndustrialKit/MaterialHandling/MasterCoil/Candidate_v034"
WRAP_MASTER = "/Game/LineBoss/Stations/Press/PR004/Candidate_v003/MaterialsPBR_v003/M_LB_PR004_NonmetalPBR_Master_v003"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr004_crane_management_candidate_v034.json"
PREFIX = "LB_PR004_V034_"
lib = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
for actor in list(actors.get_all_level_actors()):
    if actor.get_actor_label().startswith(PREFIX):
        actors.destroy_actor(actor)


def names(*values):
    return [unreal.Name(value) for value in values]


def material_instance(name, tint, roughness, texture_influence, normal_strength):
    path = f"{DEST}/{name}"
    instance = lib.load_asset(path)
    if instance is None:
        instance = tools.create_asset(name, DEST, unreal.MaterialInstanceConstant,
                                      unreal.MaterialInstanceConstantFactoryNew())
    parent = lib.load_asset(WRAP_MASTER)
    if instance is None or parent is None:
        raise RuntimeError(f"Could not create controlled material {path}")
    instance.set_editor_property("parent", parent)
    mel.set_material_instance_vector_parameter_value(instance, "SurfaceTint", unreal.LinearColor(*tint))
    for parameter, value in {
        "TextureInfluence": texture_influence,
        "TextureScale": 9.0,
        "BaseRoughness": roughness,
        "RoughTextureInfluence": 0.34,
        "Metallic": 0.0,
        "NormalStrength": normal_strength,
    }.items():
        mel.set_material_instance_scalar_parameter_value(instance, parameter, value)
    mel.update_material_instance(instance)
    lib.save_loaded_asset(instance, only_if_is_dirty=False)
    return instance


wrap = material_instance("MI_LB_MasterCoil_WovenGreyWrap_v034", (0.155, 0.175, 0.195, 1.0), 0.84, 0.44, 0.24)
overlap = material_instance("MI_LB_MasterCoil_WrapOverlap_v034", (0.052, 0.065, 0.080, 1.0), 0.88, 0.38, 0.20)
patch = material_instance("MI_LB_MasterCoil_WrapPatch_v034", (0.075, 0.125, 0.165, 1.0), 0.86, 0.40, 0.20)

all_actors = list(actors.get_all_level_actors())
packaged_components = []
station = None
for actor in all_actors:
    if actor.get_actor_label() == "LB_INT_PR004_V024_InteractiveUnpackageStation":
        station = actor
    for component in actor.get_components_by_class(unreal.StaticMeshComponent):
        mesh = component.get_editor_property("static_mesh")
        if mesh is None or "SM_LB_MasterCoil_Candidate_v004" not in mesh.get_path_name():
            continue
        component.set_material(2, wrap)
        component.set_material(3, overlap)
        component.set_material(4, patch)
        packaged_components.append(f"{actor.get_actor_label()}:{component.get_name()}")
if len(packaged_components) != 15 or station is None:
    raise RuntimeError(f"Unexpected packaged-load inventory: coils={len(packaged_components)} station={station}")

# Consolidate each reusable identity plate into a restrained 620 x 280 mm label.
label_backings = []
label_text = []
for actor in all_actors:
    label = actor.get_actor_label()
    if label.startswith("LB_COIL_LABEL_V026_"):
        actor.set_actor_scale3d(unreal.Vector(0.62, 0.28, 1.0))
        label_backings.append(label)
    elif label.startswith("LB_COIL_TEXT_V026_"):
        component = actor.get_component_by_class(unreal.TextRenderComponent)
        if component is None:
            raise RuntimeError(f"Missing text component on {label}")
        component.set_world_size(4.6 if label.endswith("_Heading") else 3.15)
        label_text.append(label)

static_components = {component.get_name(): component for component in station.get_components_by_class(unreal.StaticMeshComponent)}
text_components = {component.get_name(): component for component in station.get_components_by_class(unreal.TextRenderComponent)}
native_backing = static_components.get("PR004_WrappedCoilLabelVisual")
native_heading = text_components.get("PR004_WrappedCoilLabelHeading")
native_detail = text_components.get("PR004_WrappedCoilLabelDetail")
if any(value is None for value in (native_backing, native_heading, native_detail)):
    raise RuntimeError("Native PR-004 packaged-load identity components are incomplete")
native_backing.set_world_scale3d(unreal.Vector(0.54, 0.25, 1.0))
native_heading.set_world_size(4.4)
native_detail.set_world_size(3.0)

# Park every moving part of the 30 t support crane at the west/north service end.
# Fixed runway beams and support columns deliberately remain at their measured datums.
parked = []
motion_tags = {"LB.Motion.CraneBridge", "LB.Motion.CraneTrolley", "LB.Motion.Hoist", "LB.Motion.CHook"}
for actor in actors.get_all_level_actors():
    tags = {str(tag) for tag in actor.tags}
    if "LB.Crane.30T" not in tags or not tags.intersection(motion_tags):
        continue
    location = actor.get_actor_location()
    location.x -= 900.0
    if tags.intersection({"LB.Motion.CraneTrolley", "LB.Motion.Hoist", "LB.Motion.CHook"}):
        location.y -= 700.0
    actor.set_actor_location(location, False, False)
    parked.append(actor.get_actor_label())

hook_30t = next((actor for actor in actors.get_all_level_actors()
                 if actor.get_actor_label() == "LB_INT_FRONT_30T_CHook"), None)
link_30t = next((actor for actor in actors.get_all_level_actors()
                 if actor.get_actor_label() == "LB_INT_FRONT_30T_HookLink"), None)
identity_30t = next((actor for actor in actors.get_all_level_actors()
                     if actor.get_actor_label() == "LB_PR004_V031_30T_WestIdentity_Text"), None)
if any(value is None for value in (hook_30t, link_30t, identity_30t)):
    raise RuntimeError("Incomplete 30 t park/stow assembly")
hook_location = hook_30t.get_actor_location()
hook_location.z = 1010.0
hook_30t.set_actor_location(hook_location, False, False)
link_location = link_30t.get_actor_location()
link_location.z = 1070.0
link_30t.set_actor_location(link_location, False, False)
link_scale = link_30t.get_actor_scale3d()
link_scale.z = 0.38
link_30t.set_actor_scale3d(link_scale)
identity_30t.get_component_by_class(unreal.TextRenderComponent).set_text(
    "CAIRNWELL AUTOMOTIVE\nCR-30-01  |  SWL 30 t  |  SUPPORT")


def spot(label, location, target, intensity, radius):
    light = actors.spawn_actor_from_class(unreal.SpotLight, unreal.Vector(*location), unreal.Rotator())
    light.set_actor_label(PREFIX + label)
    light.tags = names("LB.Lighting.Candidate", "LB.Lighting.FloorTask",
                       "LB.Asset.Candidate.v034", "LB.Asset.CandidateNotPromoted")
    light.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
        light.get_actor_location(), unreal.Vector(*target)), False)
    light.spot_light_component.set_editor_properties({
        "intensity": intensity,
        "attenuation_radius": radius,
        "inner_cone_angle": 34.0,
        "outer_cone_angle": 64.0,
        "source_radius": 80.0,
        "soft_source_radius": 160.0,
        "cast_shadows": False,
        "light_color": unreal.Color(226, 235, 246, 255),
    })
    return light


lights = [
    spot("StoreFloorFill", (-6250.0, -650.0, 1120.0), (-6400.0, -2050.0, 180.0), 320.0, 2100.0),
    spot("PR004FloorFill", (-4100.0, -520.0, 1080.0), (-5050.0, -1950.0, 180.0), 430.0, 2050.0),
    spot("SupportParkFill", (-7850.0, -900.0, 1180.0), (-9000.0, -4200.0, 900.0), 240.0, 3000.0),
]


def camera(label, location, target, fov, bias):
    actor = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(PREFIX + "CAM_" + label)
    actor.tags = names("LB.Camera.Validation", "LB.Camera.Fixed.PR004Crane.v034",
                       "LB.Asset.Candidate.v034", "LB.Asset.CandidateNotPromoted")
    actor.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
        actor.get_actor_location(), unreal.Vector(*target)), False)
    component = actor.camera_component
    component.set_editor_properties({"field_of_view": fov, "aspect_ratio": 16.0 / 9.0,
                                     "constrain_aspect_ratio": True, "post_process_blend_weight": 1.0})
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
    camera("CraneManagementSouthEast", (-2850.0, 1320.0, 1080.0), (-5250.0, -2415.0, 1260.0), 68.0, -0.02),
    camera("CHookPurposeBuilt", (-6000.0, -900.0, 980.0), (-5050.0, -1850.0, 780.0), 37.0, 0.08),
    camera("CHookSideProfile", (-3950.0, -1850.0, 1050.0), (-5050.0, -1850.0, 770.0), 40.0, 0.05),
    camera("PR004OperatorOblique", (-4050.0, -420.0, 660.0), (-5050.0, -1950.0, 190.0), 50.0, 0.12),
]

if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")

payload = {
    "$schema": "line-boss/audit/press-shop-pr004-crane-management-candidate-v034/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "CRANE_HIERARCHY_LIGHTING_AND_PACKAGE_FINISH_BUILT__REGATES_REQUIRED__NOT_PROMOTED",
    "base_map": "/Game/LineBoss/Maps/LB_PressShop_PR004CraneCHookCandidate_v033",
    "map": MAP,
    "packaged_coil_component_count": len(packaged_components),
    "external_label_backing_count": len(label_backings),
    "external_label_text_count": len(label_text),
    "label_plate_dimensions_mm": [620, 280],
    "support_crane_moving_actor_count": len(parked),
    "support_crane_bridge_park_x_cm": -9100.0,
    "support_crane_trolley_park_y_cm": -4700.0,
    "support_crane_hook_stow_z_cm": 1010.0,
    "primary_40t_hook_datum_unchanged_cm": 820.0,
    "primary_hook_to_load_offset_unchanged_cm": [0.0, 150.0, -59.0],
    "floor_task_lights": [light.get_actor_label() for light in lights],
    "fixed_cameras": [camera.get_actor_label() for camera in cameras],
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR004_CRANE_V034_BUILD_PASS parked={len(parked)} coils={len(packaged_components)} map={MAP}")
unreal.SystemLibrary.quit_editor()
