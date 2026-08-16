"""Restore authored payoff-coil layer readability and restrained local task light in v045."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR005CoilFinishCandidate_v045"
ROOT = "/Game/LineBoss/Stations/Press/PR005/Candidate_v045/Materials"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr005_coil_finish_candidate_v045.json"
PAYOFF_LABEL = "LB_INT_PR005_PayoffCoil_PR-005_PayoffCoilTransferMover"
PREFIX = "LB_PR005_V045_"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
library = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

for actor in list(actors.get_all_level_actors()):
    if actor.get_actor_label().startswith(PREFIX):
        actors.destroy_actor(actor)


def simple_material(name, colour, metallic, roughness, specular=0.5):
    path = ROOT + "/" + name
    asset = library.load_asset(path)
    if asset is None:
        asset = tools.create_asset(name, ROOT, unreal.Material, unreal.MaterialFactoryNew())
    if asset is None:
        raise RuntimeError(f"Could not create {path}")
    mel.delete_all_material_expressions(asset)
    base = mel.create_material_expression(asset, unreal.MaterialExpressionConstant3Vector, -360, -100)
    base.set_editor_property("constant", unreal.LinearColor(*colour, 1.0))
    metal = mel.create_material_expression(asset, unreal.MaterialExpressionConstant, -360, 20)
    metal.set_editor_property("r", metallic)
    rough = mel.create_material_expression(asset, unreal.MaterialExpressionConstant, -360, 120)
    rough.set_editor_property("r", roughness)
    spec = mel.create_material_expression(asset, unreal.MaterialExpressionConstant, -360, 220)
    spec.set_editor_property("r", specular)
    mel.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.connect_material_property(spec, "", unreal.MaterialProperty.MP_SPECULAR)
    mel.recompile_material(asset)
    library.save_loaded_asset(asset, only_if_is_dirty=False)
    return asset


# Three restrained finishes preserve the source's real semantic material split:
# shell/lap, 28 shallow concentric face windings plus edge bands, and bore shadow.
shell = simple_material("M_PR005_CoilShell_Brushed_v045", (0.185, 0.205, 0.218), 0.82, 0.48, 0.50)
winding = simple_material("M_PR005_CoilWindingEdges_v045", (0.245, 0.262, 0.276), 0.84, 0.47, 0.48)
bore = simple_material("M_PR005_CoilBoreShadow_v045", (0.055, 0.064, 0.070), 0.60, 0.58, 0.42)

payoff = next((actor for actor in actors.get_all_level_actors()
               if actor.get_actor_label() == PAYOFF_LABEL), None)
if payoff is None or not isinstance(payoff, unreal.StaticMeshActor):
    raise RuntimeError("Authored payoff-coil actor was not found")
component = payoff.static_mesh_component
slots = component.static_mesh.get_editor_property("static_materials")
bindings = []
for index, slot in enumerate(slots):
    slot_name = str(slot.get_editor_property("imported_material_slot_name"))
    if "brushed_galvanised_steel" in slot_name:
        material = shell
    elif "winding_edges" in slot_name:
        material = winding
    elif "bore_shadow" in slot_name:
        material = bore
    else:
        raise RuntimeError(f"Unexpected payoff-coil slot {index}: {slot_name}")
    component.set_material(index, material)
    bindings.append({"index": index, "slot": slot_name, "material": material.get_path_name()})

if len(bindings) != 3:
    raise RuntimeError(f"Expected three payoff-coil semantic slots, found {len(bindings)}")
payoff.tags = list(payoff.tags) + [
    unreal.Name("LB.Asset.Candidate.v045"), unreal.Name("LB.Material.AuthoredWoundCoil"),
    unreal.Name("LB.Asset.CandidateNotPromoted")]


def spot(label, location, target, intensity, colour):
    light = actors.spawn_actor_from_class(unreal.SpotLight, unreal.Vector(*location), unreal.Rotator())
    if light is None:
        raise RuntimeError(f"Could not spawn {label}")
    light.set_actor_label(PREFIX + label)
    light.tags = [
        unreal.Name("LB.Lighting.Candidate"), unreal.Name("LB.Lighting.PR005.Task"),
        unreal.Name("LB.Asset.Candidate.v045"), unreal.Name("LB.Asset.CandidateNotPromoted")]
    light.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
        light.get_actor_location(), unreal.Vector(*target)), False)
    light.spot_light_component.set_editor_properties({
        "intensity": intensity, "attenuation_radius": 1450.0,
        "inner_cone_angle": 32.0, "outer_cone_angle": 58.0,
        "source_radius": 70.0, "soft_source_radius": 135.0,
        "cast_shadows": False, "light_color": unreal.Color(*colour, 255),
    })
    return light


# Cross-key the payoff and threader only. These deliberately modest, shadowless
# sources separate dark machinery without bleaching the surrounding floor.
lights = [
    spot("PayoffLayerTaskLight", (-4300.0, -1350.0, 690.0),
         (-4000.0, -2000.0, 165.0), 410.0, (222, 232, 244)),
    spot("ThreaderRimTaskLight", (-3450.0, -2500.0, 610.0),
         (-3820.0, -2000.0, 145.0), 360.0, (244, 226, 205)),
]


def camera(label, location, target, fov, bias):
    actor = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(PREFIX + "CAM_" + label)
    actor.tags = [
        unreal.Name("LB.Camera.Validation"), unreal.Name("LB.Camera.Fixed.PR005.v045"),
        unreal.Name("LB.Asset.Candidate.v045"), unreal.Name("LB.Asset.CandidateNotPromoted")]
    actor.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
        actor.get_actor_location(), unreal.Vector(*target)), False)
    camera_component = actor.camera_component
    camera_component.set_editor_properties({
        "field_of_view": fov, "aspect_ratio": 16.0 / 9.0,
        "constrain_aspect_ratio": True, "post_process_blend_weight": 1.0,
    })
    settings = camera_component.get_editor_property("post_process_settings")
    settings.set_editor_properties({
        "override_auto_exposure_method": True,
        "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
        "override_auto_exposure_min_brightness": True,
        "override_auto_exposure_max_brightness": True,
        "auto_exposure_min_brightness": 1.0, "auto_exposure_max_brightness": 1.0,
        "override_auto_exposure_bias": True, "auto_exposure_bias": bias,
    })
    camera_component.set_editor_property("post_process_settings", settings)
    return actor


close_camera = camera("CoilLayerClose", (-4650.0, -1180.0, 300.0),
                      (-4010.0, -2000.0, 165.0), 30.0, 0.08)
inspection_camera = camera("CoilLayerInspection", (-4380.0, -1715.0, 285.0),
                           (-4000.0, -2000.0, 165.0), 39.0, 0.04)

if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")
library.save_directory(ROOT, only_if_is_dirty=False, recursive=True)

payload = {
    "$schema": "line-boss/audit/press-shop-pr005-coil-finish-candidate-v045/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "AUTHORED_COIL_LAYER_CONTRAST_AND_RESTRAINED_TASK_LIGHT_APPLIED__FULL_REGATES_AND_FRESH_VISUAL_REVIEW_REQUIRED__NOT_PROMOTED",
    "map": MAP,
    "base_map": "/Game/LineBoss/Maps/LB_PressShop_PR005MaterialCandidate_v044",
    "payoff_actor": PAYOFF_LABEL,
    "source_geometry_contract": {
        "concentric_face_winding_objects": 28,
        "outer_edge_bands": 2,
        "lap_objects": 1,
        "bore_collars": 2,
        "triangle_count": 32188,
        "dimensions_cm": [151.2, 184.0, 185.4],
    },
    "material_bindings": bindings,
    "task_lights": [light.get_actor_label() for light in lights],
    "fixed_cameras": [close_camera.get_actor_label(), inspection_camera.get_actor_label()],
    "surface_forge_used_on_coil": False,
    "equipment_coordinates_modified": False,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR005_COIL_FINISH_V045_BUILD_PASS bindings={len(bindings)} lights={len(lights)}")
unreal.SystemLibrary.quit_editor()
