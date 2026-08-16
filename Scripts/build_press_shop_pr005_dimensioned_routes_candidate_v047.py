"""Add dimensioned, non-colliding PR-005 pedestrian and material-flow surfaces."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR005DimensionedRoutesCandidate_v047"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr005_dimensioned_routes_candidate_v047.json"
PREFIX = "LB_PR005_V047_"
CUBE = unreal.load_asset("/Engine/BasicShapes/Cube.Cube")
MATERIALS = {
    "green": unreal.load_asset("/Game/LineBoss/Stations/Press/PR005/Candidate_v046/Materials/M_PR005_FloorRoute_ProtectedGreen_v046"),
    "yellow": unreal.load_asset("/Game/LineBoss/Stations/Press/PR005/Candidate_v044/Materials/M_PR005_SafetyYellow_Coated_v044"),
    "red": unreal.load_asset("/Game/LineBoss/Stations/Press/PR005/Candidate_v046/Materials/M_PR005_FloorRoute_MaintenanceRed_v046"),
    "cyan": unreal.load_asset("/Game/LineBoss/Stations/Press/PR005/Candidate_v046/Materials/M_PR005_FloorRoute_MaterialFlowCyan_v046"),
}
if CUBE is None or any(value is None for value in MATERIALS.values()):
    raise RuntimeError("Required primitive or v044/v046 route material is missing")

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
for actor in list(actors.get_all_level_actors()):
    if actor.get_actor_label().startswith(PREFIX):
        actors.destroy_actor(actor)


def surface(label, location, size_cm, material, yaw=0.0, semantic=""):
    actor = actors.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator(0.0, 0.0, yaw))
    if actor is None:
        raise RuntimeError(f"Could not create {label}")
    actor.set_actor_label(PREFIX + label)
    actor.tags = [
        unreal.Name("LB.Asset.Candidate.v047"), unreal.Name("LB.Floor.DimensionedRoute"),
        unreal.Name("LB.Asset.CandidateNotPromoted"), unreal.Name(semantic)]
    component = actor.static_mesh_component
    component.set_static_mesh(CUBE)
    actor.set_actor_scale3d(unreal.Vector(
        size_cm[0] / 100.0, size_cm[1] / 100.0, size_cm[2] / 100.0))
    component.set_material(0, material)
    component.set_collision_profile_name(unreal.Name("NoCollision"))
    component.set_editor_property("can_ever_affect_navigation", False)
    component.set_mobility(unreal.ComponentMobility.STATIC)
    return actor


created = []


def add(*args, **kwargs):
    actor = surface(*args, **kwargs)
    created.append(actor)
    return actor


# Reference Sheet 2 requires a minimum 1,500 mm pedestrian clearance.  This
# strip occupies the protected north-side operator aisle and spans the exact
# 11,500 mm PR-005 zone without entering either adjoining station.
add("ProtectedWalkway_1500mm", (-4000.0, -1355.0, 3.00), (1150.0, 150.0, 1.2),
    MATERIALS["green"], semantic="LB.Floor.PR005.ProtectedWalkway")
add("ProtectedWalkwayEdge_Cell", (-4000.0, -1430.0, 3.75), (1150.0, 8.0, 2.0),
    MATERIALS["yellow"], semantic="LB.Floor.PR005.WalkwayEdge")
add("ProtectedWalkwayEdge_Aisle", (-4000.0, -1280.0, 3.75), (1150.0, 8.0, 2.0),
    MATERIALS["yellow"], semantic="LB.Floor.PR005.WalkwayEdge")

# Dashed red boundary separates the operator aisle from maintenance access.
for index, x in enumerate(range(-4500, -3499, 110), 1):
    add(f"MaintenanceBoundaryDash_{index:02d}", (float(x), -1475.0, 3.85),
        (70.0, 7.0, 2.0), MATERIALS["red"], semantic="LB.Floor.PR005.MaintenanceBoundary")

# The coil/strip process direction is left-to-right in the Pro plan.  A long
# cyan shaft plus a two-bar chevron makes that relationship readable in play.
add("MaterialFlowArrow_Shaft", (-4020.0, -1510.0, 3.85), (760.0, 7.0, 2.0),
    MATERIALS["cyan"], semantic="LB.Floor.PR005.MaterialFlow")
add("MaterialFlowArrow_HeadNorth", (-3618.0, -1530.0, 3.85), (70.0, 7.0, 2.0),
    MATERIALS["cyan"], yaw=35.0, semantic="LB.Floor.PR005.MaterialFlow")
add("MaterialFlowArrow_HeadSouth", (-3618.0, -1490.0, 3.85), (70.0, 7.0, 2.0),
    MATERIALS["cyan"], yaw=-35.0, semantic="LB.Floor.PR005.MaterialFlow")

if len(created) != 16:
    raise RuntimeError(f"Expected 16 route surfaces, created {len(created)}")
if any(actor.static_mesh_component.get_collision_profile_name() != unreal.Name("NoCollision")
       or actor.static_mesh_component.get_editor_property("can_ever_affect_navigation")
       for actor in created):
    raise RuntimeError("One or more route surfaces can collide or affect navigation")


route_camera = actors.spawn_actor_from_class(
    unreal.CameraActor, unreal.Vector(-4700.0, -780.0, 470.0), unreal.Rotator())
route_camera.set_actor_label(PREFIX + "CAM_DimensionedRoutes")
route_camera.tags = [
    unreal.Name("LB.Camera.Validation"), unreal.Name("LB.Camera.Fixed.PR005.v047"),
    unreal.Name("LB.Asset.Candidate.v047"), unreal.Name("LB.Asset.CandidateNotPromoted")]
route_camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
    route_camera.get_actor_location(), unreal.Vector(-4000.0, -1400.0, 8.0)), False)
camera_component = route_camera.camera_component
camera_component.set_editor_properties({
    "field_of_view": 48.0, "aspect_ratio": 16.0 / 9.0,
    "constrain_aspect_ratio": True, "post_process_blend_weight": 1.0,
})
settings = camera_component.get_editor_property("post_process_settings")
settings.set_editor_properties({
    "override_auto_exposure_method": True,
    "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
    "override_auto_exposure_min_brightness": True,
    "override_auto_exposure_max_brightness": True,
    "auto_exposure_min_brightness": 1.0, "auto_exposure_max_brightness": 1.0,
    "override_auto_exposure_bias": True, "auto_exposure_bias": 0.02,
})
camera_component.set_editor_property("post_process_settings", settings)

top_camera = actors.spawn_actor_from_class(
    unreal.CameraActor, unreal.Vector(-4000.0, -1355.0, 900.0), unreal.Rotator())
top_camera.set_actor_label(PREFIX + "CAM_RoutesTop")
top_camera.tags = list(route_camera.tags)
top_camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
    top_camera.get_actor_location(), unreal.Vector(-4000.0, -1355.0, 0.0)), False)
top_camera.camera_component.set_editor_properties({
    "field_of_view": 55.0, "aspect_ratio": 16.0 / 9.0,
    "constrain_aspect_ratio": True, "post_process_blend_weight": 1.0,
})
top_camera.camera_component.set_editor_property("post_process_settings", settings)
if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")

payload = {
    "$schema": "line-boss/audit/press-shop-pr005-dimensioned-routes-candidate-v047/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "DIMENSIONED_NON_COLLIDING_PR005_ROUTES_APPLIED__FULL_REGATES_AND_FRESH_VISUAL_REVIEW_REQUIRED__NOT_PROMOTED",
    "map": MAP,
    "base_map": "/Game/LineBoss/Maps/LB_PressShop_PR005FloorRoutesCandidate_v046",
    "walkway_dimensions_cm": [1150.0, 150.0, 1.2],
    "walkway_clearance_mm": 1500,
    "route_surface_count": len(created),
    "route_actors": [actor.get_actor_label() for actor in created],
    "collision_profile": "NoCollision",
    "can_ever_affect_navigation": False,
    "fixed_cameras": [route_camera.get_actor_label(), top_camera.get_actor_label()],
    "equipment_coordinates_modified": False,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR005_DIMENSIONED_ROUTES_V047_BUILD_PASS surfaces={len(created)}")
unreal.SystemLibrary.quit_editor()
