"""Bind native PR-010 authority and add readable release-direction detail to v098."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
TARGET = "/Game/LineBoss/Maps/LB_PressShop_PR010DetailedRuntimeCandidate_v098"
PREFIX = "LB_PR010_V098_"
OUT = ROOT / "Saved/Audits/PR010_DetailedRuntime/pr010_detailed_runtime_build_v098.json"
OUT.parent.mkdir(parents=True, exist_ok=True)
DATUM = unreal.Vector(1350.0, -2000.0, 0.0)

library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(TARGET):
    raise RuntimeError(TARGET)

for actor in list(actors_api.get_all_level_actors()):
    label = actor.get_actor_label()
    if label.startswith(PREFIX) or label.startswith("LB_PR010_V097_TEXT_") or label.startswith("LB_PR010_V097_CAM_"):
        actors_api.destroy_actor(actor)

material_root = "/Game/LineBoss/Stations/Press/PR009/Presentation_v085/Materials"
material_paths = {
    "green": f"{material_root}/M_CA_MW_PR009_LayeredCairnwellGreen_v085",
    "charcoal": f"{material_root}/M_CA_MW_PR009_LayeredFoundryCharcoal_v085",
    "yellow": f"{material_root}/M_CA_MW_PR009_LayeredSafetyYellow_v085",
    "grey": f"{material_root}/M_CA_MW_PR009_LayeredServiceGrey_v085",
    "steel": f"{material_root}/M_CA_MW_PR009_MachinedSteel_v085",
    "online": f"{material_root}/M_CA_MW_PR009_HMIScreenOnline_v085",
    "amber": f"{material_root}/M_CA_MW_PR009_AmberSafetyActive_v085",
    "glass": f"{material_root}/M_CA_MW_PR009_SensorGlass_v085",
}
materials = {key: library.load_asset(path) for key, path in material_paths.items()}
materials["clear_glass"] = library.load_asset("/Game/LineBoss/Vendor/FactoryEnvironment/Materials/MI_Glass03")
if any(value is None for value in materials.values()):
    raise RuntimeError("Missing accepted Press Shop materials")
cube = library.load_asset("/Engine/BasicShapes/Cube.Cube")
cylinder = library.load_asset("/Engine/BasicShapes/Cylinder.Cylinder")
if cube is None or cylinder is None:
    raise RuntimeError("Missing engine primitive meshes")


def tags(*values):
    return [unreal.Name(value) for value in values + (
        "LB.Station.PR010", "LB.Asset.Candidate.v098", "LB.Asset.CandidateNotPromoted", "LB.Control.ControlRoomOnly")]


def local_to_world(local_mm):
    x, y, z = local_mm
    return unreal.Vector(1350.0 + y / 10.0, -2000.0 - x / 10.0, z / 10.0)


def mesh_actor(label, mesh, location, scale, material, role, yaw=-90.0, collision="BlockAll"):
    actor = actors_api.spawn_actor_from_class(unreal.StaticMeshActor, location, unreal.Rotator(yaw=yaw))
    actor.set_actor_label(PREFIX + label)
    actor.tags = tags(role)
    component = actor.static_mesh_component
    component.set_static_mesh(mesh)
    component.set_world_scale3d(unreal.Vector(*scale))
    component.set_material(0, materials[material])
    component.set_mobility(unreal.ComponentMobility.STATIC)
    if collision == "BlockAll":
        component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
        component.set_collision_profile_name(unreal.Name("BlockAll"))
        component.set_editor_property("can_ever_affect_navigation", True)
    else:
        component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        component.set_collision_profile_name(unreal.Name("NoCollision"))
        component.set_editor_property("can_ever_affect_navigation", False)
    return actor


# Native source of truth at the signed-off datum and orientation.
station = actors_api.spawn_actor_from_class(unreal.LBPR010Station, DATUM, unreal.Rotator(yaw=-90.0))
station.set_actor_label(PREFIX + "StationAuthority")
station.tags = tags("LB.Runtime.NativeAuthority", "LB.Save.PR010", "LB.RemoteAuthority.CW.MW.CONTROL_ROOM")

# The blockout used sensor glass as a placeholder. Replace only the authored
# inspection glazing with the licensed translucent factory-glass instance.
glazing_overrides = []
for actor in list(actors_api.get_all_level_actors()):
    actor_tags = {str(value) for value in actor.tags}
    if actor.get_actor_label().startswith("LB_PR010_V097_") and "inspection_glazing" in actor_tags:
        component = actor.get_component_by_class(unreal.StaticMeshComponent)
        if component:
            component.set_material(0, materials["clear_glass"])
            glazing_overrides.append(actor.get_actor_label())

# Bind every authored moving group; stationary shell actors remain independent.
moving_roles = (
    "moving_infeed_shuttle", "moving_carrier_roller", "moving_stop_pin",
    "moving_reservation_gate", "moving_quality_spur")
bound = []
for actor in list(actors_api.get_all_level_actors()):
    if not actor.get_actor_label().startswith("LB_PR010_V097_"):
        continue
    actor_tags = {str(value) for value in actor.tags}
    role = next((value for value in moving_roles if value in actor_tags), None)
    if role and station.bind_presentation_actor(unreal.Name(actor.get_actor_label()), unreal.Name(role), actor):
        bound.append({"label": actor.get_actor_label(), "role": role})

# Approved open construction: posts and rails, never opaque guard walls.
detail = []
for lane_name, lane_x in zip("ABCD", (-4500, -1500, 1500, 4500)):
    for end_name, local_y in (("In", -2950), ("Out", 2950)):
        for side, offset in (("L", -520), ("R", 520)):
            detail.append(mesh_actor(
                f"GuardPost_Lane{lane_name}_{end_name}_{side}", cube,
                local_to_world((lane_x + offset, local_y, 550)), (0.08, 0.08, 1.10),
                "yellow", "LB.Safety.OpenMesh.Post"))
        detail.append(mesh_actor(
            f"GuardRail_Lane{lane_name}_{end_name}", cube,
            local_to_world((lane_x, local_y, 850)), (0.08, 1.04, 0.06),
            "yellow", "LB.Safety.OpenMesh.Rail"))
    detail.append(mesh_actor(
        f"Scanner_Lane{lane_name}", cylinder, local_to_world((lane_x, -3150, 120)),
        (0.14, 0.14, 0.20), "amber", "LB.Safety.Scanner", collision="NoCollision"))
    detail.append(mesh_actor(
        f"TowPoint_Lane{lane_name}", cylinder, local_to_world((lane_x, 3200, 180)),
        (0.12, 0.12, 0.32), "yellow", "LB.Service.TowPoint", yaw=0.0))

for side_name, local_x in (("West", -5200), ("East", 5200)):
    detail.append(mesh_actor(
        f"ServiceTray_{side_name}", cube, local_to_world((local_x, 0, 120)),
        (0.10, 6.2, 0.08), "steel", "LB.Service.CableTray"))

# Service-side remote HMI island and legible fictional identity.
detail.append(mesh_actor("RemoteHMI_Pedestal", cube, local_to_world((5550, -800, 650)), (0.45, 0.35, 0.65), "charcoal", "LB.HMI.Remote"))
detail.append(mesh_actor("RemoteHMI_Screen", cube, local_to_world((5550, -835, 1250)), (0.05, 0.40, 0.24), "online", "LB.HMI.Remote", collision="NoCollision"))
detail.append(mesh_actor("IdentityBackplate", cube, local_to_world((5550, -900, 1710)), (0.08, 0.82, 0.46), "charcoal", "LB.Identity.Backplate", collision="NoCollision"))


def text_actor(label, text, local_mm, size, colour):
    actor = actors_api.spawn_actor_from_class(unreal.TextRenderActor, local_to_world(local_mm), unreal.Rotator(yaw=-90.0))
    actor.set_actor_label(PREFIX + "TEXT_" + label)
    actor.tags = tags("LB.Identity.Diegetic")
    actor.text_render.set_text(text)
    actor.text_render.set_world_size(size)
    actor.text_render.set_text_render_color(colour)
    actor.text_render.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER)
    actor.text_render.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    actor.text_render.set_editor_property("can_ever_affect_navigation", False)
    return actor


identity = [
    text_actor("Corporation", "CAIRNWELL AUTOMOTIVE", (5650, -900, 1900), 7.0, unreal.Color(45, 190, 135, 255)),
    text_actor("Site", "MOORCROSS WORKS", (5650, -900, 1715), 5.2, unreal.Color(230, 235, 230, 255)),
    text_actor("Station", "PR-010  FOUR-LANE BLANK BUFFER", (5650, -900, 1545), 4.2, unreal.Color(245, 185, 35, 255)),
    text_actor("Remote", "REMOTE AUTOMATED BUFFER", (5620, -835, 1270), 3.4, unreal.Color(230, 235, 230, 255)),
]


def point_light(label, location, intensity, radius):
    actor = actors_api.spawn_actor_from_class(unreal.PointLight, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(PREFIX + "LIGHT_" + label)
    actor.tags = tags("LB.Lighting.Task.PR010")
    actor.point_light_component.set_editor_properties({
        "intensity": intensity, "attenuation_radius": radius,
        "light_color": unreal.Color(235, 244, 255, 255), "source_radius": 12.0,
        "cast_shadows": True,
    })
    return actor


lights = [
    point_light("Infeed", (1030, -2000, 520), 650.0, 850.0),
    point_light("Centre", (1400, -2000, 560), 700.0, 900.0),
    point_light("Handoff", (1800, -2000, 520), 650.0, 850.0),
    point_light("Service", (1260, -2700, 360), 320.0, 500.0),
]


def camera(label, location, target, fov):
    actor = actors_api.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(PREFIX + "CAM_" + label)
    actor.tags = tags("LB.Camera.Validation", "LB.Camera.Fixed.PR010.v098")
    actor.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(actor.get_actor_location(), unreal.Vector(*target)), False)
    actor.camera_component.set_editor_properties({"field_of_view": fov, "aspect_ratio": 16.0 / 9.0, "constrain_aspect_ratio": True})
    return actor


cameras = [
    camera("Overview", (2500, -700, 900), (1430, -2000, 115), 61),
    camera("Infeed", (520, -850, 520), (1030, -2000, 130), 56),
    camera("Handoff", (2350, -900, 560), (1750, -2000, 125), 55),
    camera("ServiceHMI", (1260, -3000, 225), (1260, -2555, 165), 35),
]

if not levels.save_current_level():
    raise RuntimeError("Could not save PR-010 v098")

failures = []
if station.get_actor_location().distance(DATUM) > 0.01:
    failures.append("native station datum mismatch")
if len(bound) != 74:
    failures.append(f"expected 74 authored moving-part bindings, found {len(bound)}")
if len(detail) < 30:
    failures.append(f"insufficient detail actors: {len(detail)}")
if len(glazing_overrides) != 4:
    failures.append(f"expected four inspection-glazing overrides, found {len(glazing_overrides)}")
if len(identity) != 4 or len(cameras) != 4:
    failures.append("identity/camera count mismatch")

result = {
    "$schema": "cairnwell/audit/pr010-detailed-runtime-build-v098/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PR010_V098_NATIVE_RUNTIME_BOUND_AND_RELEASE_DIRECTION_DETAIL_INSTALLED__GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__PR010_V098_BUILD__NOT_PROMOTED",
    "map": TARGET,
    "parent": "/Game/LineBoss/Maps/LB_PressShop_PR010BlockoutCandidate_v097",
    "native_station_count": 1,
    "native_station_datum_cm": [1350.0, -2000.0, 0.0],
    "native_station_yaw_degrees": -90.0,
    "moving_presentation_bindings": bound,
    "inspection_glazing_overrides": glazing_overrides,
    "detail_actor_count": len(detail),
    "open_guard_construction": True,
    "identity_count": len(identity),
    "camera_count": len(cameras),
    "task_light_count": len(lights),
    "press_train_datums": "TBC_NOT_INVENTED",
    "failures": failures,
    "promotion_authorized": False,
}
OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR010_V098 {result['status']} {OUT}")
if failures:
    raise RuntimeError("; ".join(failures))
