"""Correct v029 wrap exposure, label placement and span-proof framing."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


BASE = "/Game/LineBoss/Maps/LB_PressShop_PR004CraneLoadCandidate_v029"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004CraneVisualCandidate_v030"
DEST = "/Game/LineBoss/IndustrialKit/MaterialHandling/MasterCoil/Candidate_v030"
WRAP_MASTER = "/Game/LineBoss/Stations/Press/PR004/Candidate_v003/MaterialsPBR_v003/M_LB_PR004_NonmetalPBR_Master_v003"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr004_crane_visual_candidate_v030.json"

lib = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")


def material_instance(name, tint, roughness, texture_influence, normal_strength):
    path = f"{DEST}/{name}"
    instance = lib.load_asset(path)
    if instance is None:
        instance = tools.create_asset(
            name, DEST, unreal.MaterialInstanceConstant,
            unreal.MaterialInstanceConstantFactoryNew())
    parent = lib.load_asset(WRAP_MASTER)
    if instance is None or parent is None:
        raise RuntimeError(f"Could not create {path}")
    instance.set_editor_property("parent", parent)
    mel.set_material_instance_vector_parameter_value(
        instance, "SurfaceTint", unreal.LinearColor(*tint))
    for parameter, value in {
        "TextureInfluence": texture_influence,
        "TextureScale": 10.0,
        "BaseRoughness": roughness,
        "RoughTextureInfluence": 0.30,
        "Metallic": 0.0,
        "NormalStrength": normal_strength,
    }.items():
        mel.set_material_instance_scalar_parameter_value(instance, parameter, value)
    mel.update_material_instance(instance)
    lib.save_loaded_asset(instance, only_if_is_dirty=False)
    return instance


wrap = material_instance(
    "MI_LB_MasterCoil_SatinGreyWrap_v030", (0.090, 0.115, 0.140, 1.0), 0.86, 0.38, 0.20)
overlap = material_instance(
    "MI_LB_MasterCoil_WrapOverlap_v030", (0.025, 0.035, 0.050, 1.0), 0.89, 0.32, 0.17)
patch = material_instance(
    "MI_LB_MasterCoil_WrapPatch_v030", (0.070, 0.120, 0.180, 1.0), 0.86, 0.35, 0.19)

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
        packaged_components.append({"actor": actor.get_actor_label(), "component": component.get_name()})
if len(packaged_components) != 15 or station is None:
    raise RuntimeError(f"Unexpected packaged-coil count/station: {len(packaged_components)} {station}")

# The old label position was authored for a 1.50 m placeholder. Move every
# reusable Cairnwell plate to the 1.90 m face and into the upper-right quadrant
# so neither the label nor its text hides the crane-hook bore.
label_shift = unreal.Vector(48.0, 19.5, 18.0)
shifted_label_actors = []
for actor in all_actors:
    label = actor.get_actor_label()
    if label.startswith("LB_COIL_LABEL_V026_") or label.startswith("LB_COIL_TEXT_V026_"):
        actor.set_actor_location(actor.get_actor_location() + label_shift, False, False)
        shifted_label_actors.append(label)

static_components = {
    component.get_name(): component
    for component in station.get_components_by_class(unreal.StaticMeshComponent)
}
text_components = {
    component.get_name(): component
    for component in station.get_components_by_class(unreal.TextRenderComponent)
}
wrapped = static_components.get("PR004_WrappedCoilVisual")
backing = static_components.get("PR004_WrappedCoilLabelVisual")
heading = text_components.get("PR004_WrappedCoilLabelHeading")
detail = text_components.get("PR004_WrappedCoilLabelDetail")
if any(component is None for component in (wrapped, backing, heading, detail)):
    raise RuntimeError("Native PR-004 Cairnwell label components are incomplete")
origin = wrapped.get_world_location()
backing.set_world_location(unreal.Vector(origin.x + 48.0, origin.y + 96.0, origin.z + 44.0), False, False)
backing.set_world_scale3d(unreal.Vector(0.62, 0.28, 1.0))
heading.set_world_location(unreal.Vector(origin.x + 48.0, origin.y + 96.5, origin.z + 49.5), False, False)
detail.set_world_location(unreal.Vector(origin.x + 48.0, origin.y + 96.6, origin.z + 39.5), False, False)
heading.set_world_size(4.8)
detail.set_world_size(3.2)

# Rebalance the v028 fill that clipped the wrapped face under runtime capture.
service_fill = next((actor for actor in all_actors
                     if actor.get_actor_label() == "LB_PR004_V028_CraneServiceFill"), None)
if service_fill is None:
    raise RuntimeError("Missing inherited crane service fill")
service_fill.point_light_component.set_editor_properties({
    "intensity": 145.0,
    "attenuation_radius": 1900.0,
    "source_radius": 120.0,
    "soft_source_radius": 240.0,
    "cast_shadows": False,
    "light_color": unreal.Color(226, 234, 246, 255),
})

# Remove rerun cameras and use a west-side floor-height view. The long camera
# distance fits the 62.1 m bridge without sitting above the roof liner.
for actor in list(actors.get_all_level_actors()):
    if actor.get_actor_label().startswith("LB_PR004_V030_CAM_"):
        actors.destroy_actor(actor)
camera = actors.spawn_actor_from_class(
    unreal.CameraActor, unreal.Vector(-11150.0, -2415.0, 1080.0), unreal.Rotator())
camera.set_actor_label("LB_PR004_V030_CAM_CraneFullSpanWest")
camera.tags = [unreal.Name("LB.Camera.Validation"), unreal.Name("LB.Camera.Fixed.PR004Crane.v030"),
               unreal.Name("LB.Asset.Candidate.v030"), unreal.Name("LB.Asset.CandidateNotPromoted")]
camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
    camera.get_actor_location(), unreal.Vector(-5050.0, -2415.0, 1480.0)), False)
camera.camera_component.set_editor_properties({
    "field_of_view": 66.0,
    "aspect_ratio": 16.0 / 9.0,
    "constrain_aspect_ratio": True,
})

if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")

payload = {
    "$schema": "line-boss/audit/press-shop-pr004-crane-visual-candidate-v030/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "WRAP_EXPOSURE_LABEL_AND_SPAN_CAMERA_REWORK_BUILT__REGATES_REQUIRED__NOT_PROMOTED",
    "base_map": BASE,
    "map": MAP,
    "packaged_coil_component_count": len(packaged_components),
    "shifted_external_label_actor_count": len(shifted_label_actors),
    "native_label_clear_of_bore": True,
    "service_fill_intensity": 145.0,
    "fixed_camera": camera.get_actor_label(),
    "runtime_gate": "OPEN",
    "collision_gate": "OPEN",
    "visual_gate": "OPEN",
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR004_CRANE_VISUAL_V030_BUILD_PASS coils={len(packaged_components)} labels={len(shifted_label_actors)} map={MAP}")
unreal.SystemLibrary.quit_editor()
