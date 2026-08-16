"""Restore exact authored PR-005 floor-route colours and add a wide fixed review camera."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR005FloorRoutesCandidate_v046"
ROOT = "/Game/LineBoss/Stations/Press/PR005/Candidate_v046/Materials"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr005_floor_routes_candidate_v046.json"
FLOOR_LABEL = "LB_INT_PR005_FloorZoning_Static"
PREFIX = "LB_PR005_V046_"
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


def matte_material(name, colour, roughness=0.72):
    path = ROOT + "/" + name
    asset = library.load_asset(path)
    if asset is None:
        asset = tools.create_asset(name, ROOT, unreal.Material, unreal.MaterialFactoryNew())
    if asset is None:
        raise RuntimeError(f"Could not create {path}")
    mel.delete_all_material_expressions(asset)
    base = mel.create_material_expression(asset, unreal.MaterialExpressionConstant3Vector, -300, -60)
    base.set_editor_property("constant", unreal.LinearColor(*colour, 1.0))
    rough = mel.create_material_expression(asset, unreal.MaterialExpressionConstant, -300, 70)
    rough.set_editor_property("r", roughness)
    metal = mel.create_material_expression(asset, unreal.MaterialExpressionConstant, -300, 170)
    metal.set_editor_property("r", 0.0)
    mel.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    mel.recompile_material(asset)
    library.save_loaded_asset(asset, only_if_is_dirty=False)
    return asset


materials = {
    "machine_blue_service_floor_marking": matte_material(
        "M_PR005_FloorRoute_ServiceBlue_v046", (0.025, 0.105, 0.255)),
    "press_route_red_maintenance_floor_marking": matte_material(
        "M_PR005_FloorRoute_MaintenanceRed_v046", (0.42, 0.022, 0.018)),
    "action_cyan_material_flow_marking": matte_material(
        "M_PR005_FloorRoute_MaterialFlowCyan_v046", (0.015, 0.285, 0.365)),
    "floor_label_white": matte_material(
        "M_PR005_FloorRoute_LabelWhite_v046", (0.62, 0.64, 0.62), 0.76),
    "protected_walkway_green_operator_zone": matte_material(
        "M_PR005_FloorRoute_ProtectedGreen_v046", (0.035, 0.205, 0.090), 0.78),
}

floor = next((actor for actor in actors.get_all_level_actors()
              if actor.get_actor_label() == FLOOR_LABEL), None)
if floor is None or not isinstance(floor, unreal.StaticMeshActor):
    raise RuntimeError("Authored PR-005 floor-zoning actor was not found")
component = floor.static_mesh_component
slots = component.static_mesh.get_editor_property("static_materials")
bindings = []
for index, slot in enumerate(slots):
    slot_name = str(slot.get_editor_property("imported_material_slot_name"))
    selected = next((material for token, material in materials.items() if token in slot_name), None)
    if selected is None:
        continue
    component.set_material(index, selected)
    bindings.append({"index": index, "slot": slot_name, "material": selected.get_path_name()})

if len(bindings) != 5:
    raise RuntimeError(f"Expected five semantic floor bindings, found {len(bindings)}: {bindings}")
floor.tags = list(floor.tags) + [
    unreal.Name("LB.Asset.Candidate.v046"), unreal.Name("LB.Floor.SemanticRoutes"),
    unreal.Name("LB.Asset.CandidateNotPromoted")]


def camera(label, location, target, fov, bias):
    actor = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(PREFIX + "CAM_" + label)
    actor.tags = [
        unreal.Name("LB.Camera.Validation"), unreal.Name("LB.Camera.Fixed.PR005.v046"),
        unreal.Name("LB.Asset.Candidate.v046"), unreal.Name("LB.Asset.CandidateNotPromoted")]
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


wide = camera("PR005WholeLine", (-5200.0, -760.0, 720.0),
              (-3920.0, -2010.0, 120.0), 52.0, 0.06)
routes = camera("PR005FloorRoutes", (-4800.0, -1030.0, 430.0),
                (-4000.0, -1660.0, 15.0), 46.0, 0.04)

if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")
library.save_directory(ROOT, only_if_is_dirty=False, recursive=True)

payload = {
    "$schema": "line-boss/audit/press-shop-pr005-floor-routes-candidate-v046/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "EXACT_SEMANTIC_FLOOR_ROUTE_BINDINGS_APPLIED__FULL_REGATES_AND_FRESH_VISUAL_REVIEW_REQUIRED__NOT_PROMOTED",
    "map": MAP,
    "base_map": "/Game/LineBoss/Maps/LB_PressShop_PR005CoilFinishCandidate_v045",
    "floor_actor": FLOOR_LABEL,
    "material_bindings": bindings,
    "retained_safety_yellow_slot": "PR005_floor_safety_yellow",
    "fixed_cameras": [wide.get_actor_label(), routes.get_actor_label()],
    "equipment_coordinates_modified": False,
    "collision_or_navigation_modified": False,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR005_FLOOR_ROUTES_V046_BUILD_PASS bindings={len(bindings)}")
unreal.SystemLibrary.quit_editor()
