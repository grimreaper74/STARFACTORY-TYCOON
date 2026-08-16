"""Restore readable semantic materials to the authored PR-005 hydraulic routing."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR005ServiceRoutingCandidate_v050"
ROOT = "/Game/LineBoss/Stations/Press/PR005/Candidate_v050/Materials"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr005_service_routing_candidate_v050.json"
ACTOR_LABEL = "LB_INT_PR005_HydraulicRouting_Static"
PREFIX = "LB_PR005_V050_"
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


def material(name, colour, metallic, roughness):
    path = ROOT + "/" + name
    asset = library.load_asset(path)
    if asset is None:
        asset = tools.create_asset(name, ROOT, unreal.Material, unreal.MaterialFactoryNew())
    if asset is None:
        raise RuntimeError(f"Could not create {path}")
    mel.delete_all_material_expressions(asset)
    base = mel.create_material_expression(asset, unreal.MaterialExpressionConstant3Vector, -300, -70)
    base.set_editor_property("constant", unreal.LinearColor(*colour, 1.0))
    metal = mel.create_material_expression(asset, unreal.MaterialExpressionConstant, -300, 45)
    metal.set_editor_property("r", metallic)
    rough = mel.create_material_expression(asset, unreal.MaterialExpressionConstant, -300, 145)
    rough.set_editor_property("r", roughness)
    mel.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(asset)
    library.save_loaded_asset(asset, only_if_is_dirty=False)
    return asset


materials = {
    "PR005_pressure_identification": material(
        "M_PR005_Service_PressureRed_v050", (0.34, 0.010, 0.006), 0.15, 0.58),
    "PR005_service_union_steel": material(
        "M_PR005_Service_UnionSteel_v050", (0.22, 0.26, 0.28), 0.86, 0.34),
    "PR005_return_identification": material(
        "M_PR005_Service_ReturnBlue_v050", (0.008, 0.065, 0.30), 0.12, 0.58),
    "PR005_hydraulic_hose": material(
        "M_PR005_Service_HoseRubber_v050", (0.008, 0.010, 0.012), 0.0, 0.78),
    "PR005_crossing_grip": material(
        "M_PR005_Service_CrossingGrip_v050", (0.025, 0.030, 0.033), 0.32, 0.72),
    "PR005_crossing_tread": material(
        "M_PR005_Service_CrossingTread_v050", (0.12, 0.14, 0.15), 0.76, 0.52),
    "PR005_galvanised_carrier": material(
        "M_PR005_Service_GalvanisedCarrier_v050", (0.30, 0.34, 0.35), 0.78, 0.46),
}

routing = next((actor for actor in actors.get_all_level_actors()
                if actor.get_actor_label() == ACTOR_LABEL), None)
if routing is None or not isinstance(routing, unreal.StaticMeshActor):
    raise RuntimeError("Missing authored PR-005 hydraulic-routing actor")
component = routing.static_mesh_component
slots = component.static_mesh.get_editor_property("static_materials")
bindings = []
for index, slot in enumerate(slots):
    slot_name = str(slot.get_editor_property("imported_material_slot_name"))
    selected = next((asset for token, asset in materials.items() if token in slot_name), None)
    if selected is None:
        continue
    component.set_material(index, selected)
    bindings.append({"index": index, "slot": slot_name, "material": selected.get_path_name()})
if len(bindings) != 7:
    raise RuntimeError(f"Expected seven semantic service bindings, found {len(bindings)}: {bindings}")
routing.tags = list(routing.tags) + [
    unreal.Name("LB.Asset.Candidate.v050"), unreal.Name("LB.Asset.CandidateNotPromoted"),
    unreal.Name("LB.Service.HydraulicRouting.SemanticFinish")]


def camera(label, location, target, fov, bias):
    actor = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(PREFIX + "CAM_" + label)
    actor.tags = [
        unreal.Name("LB.Camera.Validation"), unreal.Name("LB.Camera.Fixed.PR005.v050"),
        unreal.Name("LB.Asset.Candidate.v050"), unreal.Name("LB.Asset.CandidateNotPromoted")]
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


cameras = [
    camera("ServiceRoutingPlayer", (-4700.0, -720.0, 285.0), (-4020.0, -1690.0, 55.0), 44.0, 0.06),
    camera("ServiceRoutingElevated", (-4750.0, -850.0, 570.0), (-4000.0, -1720.0, 30.0), 47.0, 0.05),
    camera("ServiceRoutingWholeLine", (-5200.0, -720.0, 700.0), (-3920.0, -1900.0, 110.0), 54.0, 0.06),
]

if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")
library.save_directory(ROOT, only_if_is_dirty=False, recursive=True)
payload = {
    "$schema": "line-boss/audit/press-shop-pr005-service-routing-candidate-v050/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "SEVEN_SEMANTIC_HYDRAULIC_SERVICE_MATERIALS_BOUND__FULL_RUNTIME_AND_VISUAL_GATES_REQUIRED__NOT_PROMOTED",
    "map": MAP, "base_map": "/Game/LineBoss/Maps/LB_PressShop_PR005FloorJunctionCandidate_v049",
    "actor": ACTOR_LABEL, "material_bindings": bindings,
    "authored_geometry_preserved": True, "equipment_coordinates_modified": False,
    "collision_or_navigation_modified": False,
    "fixed_cameras": [actor.get_actor_label() for actor in cameras],
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR005_SERVICE_ROUTING_V050_BUILD_PASS bindings={len(bindings)} map={MAP}")
unreal.SystemLibrary.quit_editor()
