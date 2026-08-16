"""Refine packaged-coil fibre/overlap/pad response without changing geometry."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004WrapFinishCandidate_v040"
DEST = "/Game/LineBoss/IndustrialKit/MaterialHandling/MasterCoil/Candidate_v040"
MASTER = "/Game/LineBoss/Stations/Press/PR004/Candidate_v003/MaterialsPBR_v003/M_LB_PR004_NonmetalPBR_Master_v003"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr004_wrap_finish_candidate_v040.json"
PREFIX = "LB_PR004_V040_"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
lib = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
for actor in list(actors.get_all_level_actors()):
    if actor.get_actor_label().startswith(PREFIX):
        actors.destroy_actor(actor)


def material(name, tint, roughness, influence, scale, normal, rough_variation):
    path = f"{DEST}/{name}"
    value = lib.load_asset(path)
    if value is None:
        value = tools.create_asset(name, DEST, unreal.MaterialInstanceConstant,
                                   unreal.MaterialInstanceConstantFactoryNew())
    parent = lib.load_asset(MASTER)
    if value is None or parent is None:
        raise RuntimeError(f"Could not create {path}")
    value.set_editor_property("parent", parent)
    mel.set_material_instance_vector_parameter_value(value, "SurfaceTint", unreal.LinearColor(*tint))
    for key, scalar in {
        "TextureInfluence": influence,
        "TextureScale": scale,
        "BaseRoughness": roughness,
        "RoughTextureInfluence": rough_variation,
        "Metallic": 0.0,
        "NormalStrength": normal,
    }.items():
        mel.set_material_instance_scalar_parameter_value(value, key, scalar)
    mel.update_material_instance(value)
    lib.save_loaded_asset(value, only_if_is_dirty=False)
    return value


wrap = material("MI_LB_MasterCoil_WovenSilverWrap_v040",
                (0.190, 0.215, 0.245, 1.0), 0.76, 0.56, 18.0, 0.34, 0.42)
overlap = material("MI_LB_MasterCoil_WrapOverlap_v040",
                   (0.110, 0.135, 0.160, 1.0), 0.82, 0.48, 16.0, 0.28, 0.38)
patch = material("MI_LB_MasterCoil_WrapPatch_v040",
                 (0.155, 0.180, 0.210, 1.0), 0.84, 0.52, 20.0, 0.32, 0.44)
fibre = material("MI_LB_MasterCoil_CompressedFibre_v040",
                 (0.205, 0.095, 0.030, 1.0), 0.92, 0.60, 24.0, 0.40, 0.50)

packaged = []
for actor in actors.get_all_level_actors():
    for component in actor.get_components_by_class(unreal.StaticMeshComponent):
        mesh = component.get_editor_property("static_mesh")
        if mesh is None or "SM_LB_MasterCoil_Candidate_v004" not in mesh.get_path_name():
            continue
        component.set_material(2, wrap)
        component.set_material(3, overlap)
        component.set_material(4, patch)
        component.set_material(6, fibre)
        packaged.append(f"{actor.get_actor_label()}:{component.get_name()}")


def camera(label, location, target, fov, bias):
    camera_actor = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    camera_actor.set_actor_label(PREFIX + "CAM_" + label)
    camera_actor.tags = [unreal.Name("LB.Camera.Validation"), unreal.Name("LB.Camera.Fixed.WrapFinish.v040"),
                         unreal.Name("LB.Asset.Candidate.v040"), unreal.Name("LB.Asset.CandidateNotPromoted")]
    camera_actor.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
        camera_actor.get_actor_location(), unreal.Vector(*target)), False)
    component = camera_actor.camera_component
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
    return camera_actor


close_camera = camera("PackageMaterialClose", (-4520.0, -1370.0, 330.0),
                      (-5050.0, -1925.0, 145.0), 39.0, -0.02)

# A restrained overhead-side task source reveals the cylindrical wrap response
# that the inherited south-only fill leaves black. It is aimed at the package,
# not at the camera, and cannot affect collision or navigation.
task_light = actors.spawn_actor_from_class(
    unreal.SpotLight, unreal.Vector(-4200.0, -3100.0, 950.0), unreal.Rotator())
task_light.set_actor_label(PREFIX + "PackageSurfaceTaskLight")
task_light.tags = [unreal.Name("LB.Lighting.Candidate"), unreal.Name("LB.Lighting.PackageTask"),
                   unreal.Name("LB.Asset.Candidate.v040"), unreal.Name("LB.Asset.CandidateNotPromoted")]
task_light.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
    task_light.get_actor_location(), unreal.Vector(-5050.0, -2000.0, 160.0)), False)
task_light.spot_light_component.set_editor_properties({
    "intensity": 480.0,
    "attenuation_radius": 1900.0,
    "inner_cone_angle": 34.0,
    "outer_cone_angle": 62.0,
    "source_radius": 90.0,
    "soft_source_radius": 180.0,
    "cast_shadows": False,
    "light_color": unreal.Color(226, 234, 244, 255),
})

if len(packaged) != 15:
    raise RuntimeError(f"Unexpected packaged presentation count {len(packaged)}")
if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")

payload = {
    "$schema": "line-boss/audit/press-shop-pr004-wrap-finish-candidate-v040/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "ISOLATED_DIMENSION_PRESERVING_PACKAGE_SURFACE_REWORK__REGATES_REQUIRED__NOT_PROMOTED",
    "base_map": "/Game/LineBoss/Maps/LB_PressShop_PR004TraceabilityCandidate_v039",
    "map": MAP,
    "packaged_component_count": len(packaged),
    "geometry_changed": False,
    "material_slots_changed": [2, 3, 4, 6],
    "materials": [wrap.get_path_name(), overlap.get_path_name(), patch.get_path_name(), fibre.get_path_name()],
    "fixed_camera": close_camera.get_actor_label(),
    "package_task_light": task_light.get_actor_label(),
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR004_WRAP_FINISH_V040_BUILD_PASS coils={len(packaged)}")
unreal.SystemLibrary.quit_editor()
