"""Add release-facing ceiling context and fixed crane review cameras to v028."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


BASE = "/Game/LineBoss/Maps/LB_PressShop_PR004CraneRuntimeCandidate_v027"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004CraneVisualCandidate_v028"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr004_crane_visual_candidate_v028.json"
PREFIX = "LB_PR004_V028_"
CUBE = unreal.load_asset("/Engine/BasicShapes/Cube.Cube")
GIRDER = unreal.load_asset(
    "/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/"
    "SM_LB_Crane_BridgeGirder_4500_v001.SM_LB_Crane_BridgeGirder_4500_v001")
CEILING_MATERIAL = unreal.load_asset(
    "/Game/LineBoss/Materials/FrontEnd/MI_LB_Wall_Concrete.MI_LB_Wall_Concrete")
ROOF_MATERIAL = unreal.load_asset(
    "/Game/LineBoss/Materials/M_LB_ShellCharcoal.M_LB_ShellCharcoal")
BEAM_MATERIAL = unreal.load_asset(
    "/Game/LineBoss/Materials/M_LB_StructureSteel.M_LB_StructureSteel")
if (CUBE is None or GIRDER is None or CEILING_MATERIAL is None
        or ROOF_MATERIAL is None or BEAM_MATERIAL is None):
    raise RuntimeError("Missing cube or release material required for the v028 ceiling")

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

for actor in list(actors.get_all_level_actors()):
    if (actor.get_actor_label().startswith(PREFIX)
            or actor.get_actor_label() in {
                "LB_INT_FRONT_40T_BridgeGirder_1",
                "LB_INT_FRONT_40T_BridgeGirder_2",
                "LB_INT_FRONT_30T_BridgeGirder_1",
            }):
        actors.destroy_actor(actor)


def tags(*values):
    return [unreal.Name(value) for value in values]


def cube(label, location, size, material, actor_tags):
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(PREFIX + label)
    actor.tags = tags(*actor_tags, "LB.Asset.Candidate.v028", "LB.Asset.CandidateNotPromoted")
    component = actor.static_mesh_component
    component.set_static_mesh(CUBE)
    component.set_material(0, material)
    component.set_collision_profile_name(unreal.Name("NoCollision"))
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    body_instance = component.get_editor_property("body_instance")
    body_instance.set_editor_property("collision_enabled", unreal.CollisionEnabled.NO_COLLISION)
    component.set_editor_property("body_instance", body_instance)
    component.set_editor_property("can_ever_affect_navigation", False)
    component.set_editor_property("cast_shadow", False)
    actor.set_actor_scale3d(unreal.Vector(size[0] / 100.0, size[1] / 100.0, size[2] / 100.0))
    return actor


# The inherited crane used one 4.5 m girder module at the centre of a 62.1 m
# runway span.  Build the actual bridge from dimensioned welded modules between
# both end trucks; the small per-module length trim closes the span exactly.
south_rail_y = -5520.0
north_rail_y = 690.0
bridge_span_cm = north_rail_y - south_rail_y
bridge_segment_count = 14
bridge_segment_length_cm = bridge_span_cm / bridge_segment_count
bridge_segment_scale_y = bridge_segment_length_cm / 450.0
bridge_modules = []
for girder_index, x in enumerate((-5155.0, -4945.0), 1):
    for segment_index in range(bridge_segment_count):
        y = south_rail_y + (segment_index + 0.5) * bridge_segment_length_cm
        actor = actors.spawn_actor_from_class(
            unreal.StaticMeshActor, unreal.Vector(x, y, 1500.0), unreal.Rotator())
        actor.set_actor_label(PREFIX + f"40T_BridgeGirder_{girder_index}_Segment_{segment_index + 1:02d}")
        actor.tags = tags(
            "LB.Motion.CraneBridge", "LB.Crane.40T", "LB.Animation.Pivot.Bridge",
            "LB.Module.CraneBridgeSegment", "LB.Asset.Candidate.v028",
            "LB.Asset.CandidateNotPromoted")
        component = actor.static_mesh_component
        component.set_static_mesh(GIRDER)
        component.set_mobility(unreal.ComponentMobility.MOVABLE)
        component.set_editor_property("can_ever_affect_navigation", False)
        actor.set_actor_scale3d(unreal.Vector(1.0, bridge_segment_scale_y, 1.0))
        bridge_modules.append(actor)

bridge_cross_ties = []
for tie_index in range(8):
    y = south_rail_y + tie_index * (bridge_span_cm / 7.0)
    tie = cube(
        f"40T_BridgeCrossTie_{tie_index + 1:02d}", (-5050.0, y, 1494.0),
        (270.0, 22.0, 42.0), BEAM_MATERIAL,
        ("LB.Motion.CraneBridge", "LB.Crane.40T", "LB.Module.CraneBridgeCrossTie"))
    tie.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    bridge_cross_ties.append(tie)

# One operational identity plate replaces reliance on the repeated blank
# module insets and keeps the diegetic Cairnwell/Moorcross identity explicit.
crane_identity_backing = cube(
    "40T_CraneIdentityBacking", (-4905.0, -2415.0, 1505.0),
    (10.0, 310.0, 64.0), BEAM_MATERIAL,
    ("LB.Motion.CraneBridge", "LB.Crane.40T", "LB.Module.CraneIdentity"))
crane_identity_backing.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE)
crane_identity = actors.spawn_actor_from_class(
    unreal.TextRenderActor, unreal.Vector(-4898.0, -2415.0, 1505.0), unreal.Rotator())
crane_identity.set_actor_label(PREFIX + "40T_CraneIdentityText")
crane_identity.tags = tags(
    "LB.Motion.CraneBridge", "LB.Crane.40T", "LB.Module.CraneIdentity",
    "LB.Asset.Candidate.v028", "LB.Asset.CandidateNotPromoted")
identity_text = crane_identity.text_render
identity_text.set_editor_properties({
    "text": "CAIRNWELL AUTOMOTIVE\nCR-40-01  |  SWL 40 t",
    "world_size": 18.0,
    "horizontal_alignment": unreal.HorizTextAligment.EHTA_CENTER,
    "vertical_alignment": unreal.VerticalTextAligment.EVRTA_TEXT_CENTER,
    "text_render_color": unreal.Color(238, 242, 246, 255),
    "can_ever_affect_navigation": False,
})
identity_text.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
identity_text.set_mobility(unreal.ComponentMobility.MOVABLE)

bridge_30t_modules = []
for segment_index in range(bridge_segment_count):
    y = south_rail_y + (segment_index + 0.5) * bridge_segment_length_cm
    actor = actors.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(-8200.0, y, 1500.0), unreal.Rotator())
    actor.set_actor_label(PREFIX + f"30T_BridgeGirder_Segment_{segment_index + 1:02d}")
    actor.tags = tags(
        "LB.Motion.CraneBridge", "LB.Crane.30T", "LB.Animation.Pivot.Bridge",
        "LB.Module.CraneBridgeSegment", "LB.Asset.Candidate.v028",
        "LB.Asset.CandidateNotPromoted")
    actor.static_mesh_component.set_static_mesh(GIRDER)
    actor.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    actor.static_mesh_component.set_editor_property("can_ever_affect_navigation", False)
    actor.set_actor_scale3d(unreal.Vector(1.0, bridge_segment_scale_y, 1.0))
    bridge_30t_modules.append(actor)


# The inherited front-end cutaway deliberately had no physical roof.  That
# reads as a black void from eye-level crane views, so provide a lightweight
# modular inner roof liner above the crane/luminaire clearance envelope.
roof_panels = []
panel_size = (1700.0, 1750.0, 12.0)
for ix, x in enumerate((-10150.0, -8450.0, -6750.0, -5050.0, -3350.0), 1):
    for iy, y in enumerate((-5125.0, -3375.0, -1625.0, 125.0), 1):
        roof_panels.append(cube(
            f"RoofLiner_{ix:02d}_{iy:02d}", (x, y, 1900.0), panel_size,
            ROOF_MATERIAL, ("LB.Module.FactoryRoofLiner", "LB.Streaming.Press.FrontEnd")))

roof_beams = []
for index, x in enumerate((-11000.0, -9300.0, -7600.0, -5900.0, -4200.0, -2500.0), 1):
    roof_beams.append(cube(
        f"RoofBeam_NS_{index:02d}", (x, -2500.0, 1875.0), (20.0, 7000.0, 55.0),
        BEAM_MATERIAL, ("LB.Module.FactoryRoofPurlin", "LB.Streaming.Press.FrontEnd")))
for index, y in enumerate((-6000.0, -4250.0, -2500.0, -750.0, 1000.0), 1):
    roof_beams.append(cube(
        f"RoofBeam_EW_{index:02d}", (-6750.0, y, 1875.0), (8500.0, 20.0, 55.0),
        BEAM_MATERIAL, ("LB.Module.FactoryRoofPurlin", "LB.Streaming.Press.FrontEnd")))

# Close the south-shell cutaway void behind the crane path with modular inner
# wall liners.  These sit on the actual outer boundary and are non-colliding in
# this visual candidate so the already-passed navigation envelope is unchanged.
south_wall_panels = []
for index, x in enumerate((-10150.0, -8450.0, -6750.0, -5050.0, -3350.0), 1):
    south_wall_panels.append(cube(
        f"SouthWallLiner_{index:02d}", (x, -5994.0, 950.0), (1700.0, 12.0, 1900.0),
        CEILING_MATERIAL, ("LB.Module.FactoryWallLiner", "LB.Streaming.Press.FrontEnd")))

# A restrained shadowless service-bay fill makes the hook engagement, package
# label and coil bore readable without flattening the existing authored lamps.
crane_fill = actors.spawn_actor_from_class(
    unreal.PointLight, unreal.Vector(-5600.0, -900.0, 1250.0), unreal.Rotator())
crane_fill.set_actor_label(PREFIX + "CraneServiceFill")
crane_fill.tags = tags("LB.Lighting.Candidate", "LB.Streaming.Press.FrontEnd",
                       "LB.Asset.Candidate.v028", "LB.Asset.CandidateNotPromoted")
crane_fill.point_light_component.set_editor_properties({
    "intensity": 500.0,
    "attenuation_radius": 2200.0,
    "source_radius": 90.0,
    "soft_source_radius": 180.0,
    "cast_shadows": False,
    "light_color": unreal.Color(235, 241, 250, 255),
})


def add_camera(label, location, target, fov):
    camera = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    camera.set_actor_label(PREFIX + label)
    camera.tags = tags("LB.Camera.Validation", "LB.Camera.Fixed.PR004Crane.v028",
                       "LB.Asset.Candidate.v028", "LB.Asset.CandidateNotPromoted")
    camera.set_actor_rotation(
        unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(), unreal.Vector(*target)), False)
    camera.camera_component.set_editor_properties({
        "field_of_view": fov,
        "aspect_ratio": 16.0 / 9.0,
        "constrain_aspect_ratio": True,
    })
    return camera


cameras = [
    add_camera("CAM_CraneFullSpan", (-2500.0, -2415.0, 1250.0), (-5050.0, -2415.0, 1500.0), 105.0),
    add_camera("CAM_CraneSpanOblique", (-2500.0, 850.0, 1250.0), (-5050.0, -2415.0, 1450.0), 82.0),
    add_camera("CAM_CraneCarryWide", (-6900.0, -250.0, 1120.0), (-5050.0, -1900.0, 840.0), 44.0),
    add_camera("CAM_CHookEngagement", (-5900.0, -850.0, 900.0), (-5050.0, -1850.0, 730.0), 34.0),
    add_camera("CAM_PR004Deposit", (-5850.0, -330.0, 720.0), (-5050.0, -2000.0, 170.0), 44.0),
]

if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")

payload = {
    "$schema": "line-boss/audit/press-shop-pr004-crane-visual-candidate-v028/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "CRANE_VISUAL_REWORK_BUILT__RUNTIME_AND_VISUAL_REGATES_REQUIRED__NOT_PROMOTED",
    "base_map": BASE,
    "map": MAP,
    "roof_liner_panels": len(roof_panels),
    "roof_purlins": len(roof_beams),
    "south_wall_liner_panels": len(south_wall_panels),
    "crane_service_fill_lights": 1,
    "roof_clearance_cm": 1900.0,
    "fixed_cameras": [camera.get_actor_label() for camera in cameras],
    "c_hook_bore_centre_offset_cm": 59.0,
    "crane_bridge": {
        "span_cm": bridge_span_cm,
        "south_end_truck_y_cm": south_rail_y,
        "north_end_truck_y_cm": north_rail_y,
        "girder_count": 2,
        "segments_per_girder": bridge_segment_count,
        "segment_length_cm": bridge_segment_length_cm,
        "segment_modules": len(bridge_modules),
        "cross_ties": len(bridge_cross_ties),
        "secondary_30t_single_girder_segments": len(bridge_30t_modules),
        "diegetic_identity": "CAIRNWELL AUTOMOTIVE / CR-40-01 / SWL 40 t",
    },
    "collision_policy": "Roof liner and purlins are visual overhead context with collision disabled; floor/nav envelope unchanged.",
    "runtime_gate": "OPEN",
    "visual_gate": "OPEN",
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR004_CRANE_V028_BUILD_PASS map={MAP} output={OUT}")
