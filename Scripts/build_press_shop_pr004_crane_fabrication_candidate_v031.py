"""Add fabrication hierarchy, service detail and balanced lighting to v031."""

import json
import math
from datetime import datetime, timezone
from pathlib import Path

import unreal


BASE = "/Game/LineBoss/Maps/LB_PressShop_PR004CraneVisualCandidate_v030"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004CraneFabricationCandidate_v031"
DEST = "/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/Candidate_v031"
MASTER = "/Game/LineBoss/Stations/Press/PR004/Candidate_v003/MaterialsPBR_v003"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr004_crane_fabrication_candidate_v031.json"
PREFIX = "LB_PR004_V031_"

lib = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
CUBE = unreal.load_asset("/Engine/BasicShapes/Cube")
CYLINDER = unreal.load_asset("/Engine/BasicShapes/Cylinder")
if CUBE is None or CYLINDER is None:
    raise RuntimeError("Missing Engine fabrication primitives")

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

for actor in list(actors.get_all_level_actors()):
    if actor.get_actor_label().startswith(PREFIX):
        actors.destroy_actor(actor)


def tags(*values):
    return [unreal.Name(value) for value in values]


def instance(name, kind, tint, roughness, metallic, texture, normal):
    path = f"{DEST}/{name}"
    result = lib.load_asset(path)
    if result is None:
        result = tools.create_asset(
            name, DEST, unreal.MaterialInstanceConstant,
            unreal.MaterialInstanceConstantFactoryNew())
    parent = lib.load_asset(f"{MASTER}/M_LB_PR004_{kind}_Master_v003")
    if result is None or parent is None:
        raise RuntimeError(f"Could not create {path}")
    result.set_editor_property("parent", parent)
    mel.set_material_instance_vector_parameter_value(
        result, "SurfaceTint", unreal.LinearColor(*tint))
    for parameter, value in {
        "TextureInfluence": texture,
        "TextureScale": 7.5,
        "BaseRoughness": roughness,
        "RoughTextureInfluence": 0.34,
        "Metallic": metallic,
        "NormalStrength": normal,
    }.items():
        mel.set_material_instance_scalar_parameter_value(result, parameter, value)
    mel.update_material_instance(result)
    lib.save_loaded_asset(result, only_if_is_dirty=False)
    return result


yellow = instance("MI_LB_Crane_RAL1023_Aged_v031", "MetalPBR",
                  (0.52, 0.27, 0.003, 1.0), 0.62, 0.18, 0.30, 0.18)
dark = instance("MI_LB_Crane_DarkSteel_v031", "MetalPBR",
                (0.015, 0.020, 0.026, 1.0), 0.70, 0.68, 0.24, 0.16)
exposed = instance("MI_LB_Crane_ExposedSteel_v031", "MetalPBR",
                   (0.22, 0.25, 0.28, 1.0), 0.44, 1.0, 0.20, 0.12)
grease = instance("MI_LB_Crane_GreaseResidue_v031", "NonmetalPBR",
                  (0.008, 0.004, 0.001, 1.0), 0.28, 0.0, 0.24, 0.14)


def cube(label, location, dimensions, material, actor_tags, mobility=unreal.ComponentMobility.MOVABLE):
    actor = actors.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(PREFIX + label)
    actor.tags = tags(*actor_tags, "LB.Asset.Candidate.v031", "LB.Asset.CandidateNotPromoted")
    actor.set_actor_scale3d(unreal.Vector(
        dimensions[0] / 100.0, dimensions[1] / 100.0, dimensions[2] / 100.0))
    component = actor.static_mesh_component
    component.set_static_mesh(CUBE)
    component.set_material(0, material)
    component.set_mobility(mobility)
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_collision_profile_name(unreal.Name("NoCollision"))
    component.set_editor_property("can_ever_affect_navigation", False)
    return actor


def cylinder_between(label, start, end, radius, material, actor_tags):
    a = unreal.Vector(*start)
    b = unreal.Vector(*end)
    delta = b - a
    length = delta.length()
    actor = actors.spawn_actor_from_class(
        unreal.StaticMeshActor, (a + b) * 0.5, unreal.Rotator())
    actor.set_actor_label(PREFIX + label)
    actor.tags = tags(*actor_tags, "LB.Asset.Candidate.v031", "LB.Asset.CandidateNotPromoted")
    actor.set_actor_rotation(unreal.MathLibrary.make_rot_from_z(delta), False)
    actor.set_actor_scale3d(unreal.Vector(radius / 50.0, radius / 50.0, length / 100.0))
    component = actor.static_mesh_component
    component.set_static_mesh(CYLINDER)
    component.set_material(0, material)
    component.set_mobility(unreal.ComponentMobility.MOVABLE)
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_collision_profile_name(unreal.Name("NoCollision"))
    component.set_editor_property("can_ever_affect_navigation", False)
    return actor


bridge_tags_40 = ("LB.Motion.CraneBridge", "LB.Crane.40T", "LB.Module.CraneFabrication")
bridge_tags_30 = ("LB.Motion.CraneBridge", "LB.Crane.30T", "LB.Module.CraneFabrication")
south_y = -5520.0
north_y = 690.0
span = north_y - south_y
segment = span / 14.0

# Replace clean material overrides on all inherited bridge modules without
# changing their proven positions, bounds, scale or motion tags.
overridden_bridge_components = []
for actor in actors.get_all_level_actors():
    label = actor.get_actor_label()
    if not (label.startswith("LB_PR004_V028_40T_BridgeGirder_")
            or label.startswith("LB_PR004_V028_30T_BridgeGirder_")):
        continue
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    component.set_material(0, yellow)
    component.set_material(1, dark)
    component.set_material(2, exposed)
    overridden_bridge_components.append(label)

# Authored joint splice plates turn the fourteen modules into a believable
# welded/bolted bridge rather than fourteen copied signs.
splice_plates = []
for crane, xs, crane_tags in (
    ("40T", (-5225.0, -4875.0), bridge_tags_40),
    ("30T", (-8270.0, -8130.0), bridge_tags_30),
):
    for joint in range(1, 14):
        y = south_y + joint * segment
        for side, x in enumerate(xs, 1):
            splice_plates.append(cube(
                f"{crane}_Splice_{joint:02d}_{side}", (x, y, 1500.0),
                (5.0, 18.0, 132.0), dark, crane_tags))

running_rails = []
for index, (label, x, crane_tags) in enumerate((
    ("40T_Rail_A", -5155.0, bridge_tags_40),
    ("40T_Rail_B", -4945.0, bridge_tags_40),
    ("30T_Rail", -8200.0, bridge_tags_30),
), 1):
    running_rails.append(cube(label, (x, (south_y+north_y)*0.5, 1584.0),
                              (8.0, span, 8.0), exposed, crane_tags))
    cube(label + "_GreaseWitness", (x, (south_y+north_y)*0.5, 1588.5),
         (9.0, span * 0.82, 1.5), grease, crane_tags)

# 40 t festoon rail, hangers and six restrained cable loops.
festoon = [cube("40T_FestoonRail", (-4868.0, (south_y+north_y)*0.5, 1545.0),
                (5.0, span, 6.0), exposed, bridge_tags_40)]
loop_centres = [-4720.0, -4280.0, -3840.0, -3400.0, -2960.0, -2520.0]
for loop_index, centre_y in enumerate(loop_centres, 1):
    hanger_y = centre_y - 190.0
    next_y = centre_y + 190.0
    for suffix, y in (("A", hanger_y), ("B", next_y)):
        festoon.append(cube(
            f"40T_FestoonHanger_{loop_index:02d}_{suffix}", (-4868.0, y, 1518.0),
            (12.0, 6.0, 54.0), dark, bridge_tags_40))
    points = [
        (-4868.0, hanger_y, 1510.0),
        (-4868.0, centre_y - 85.0, 1405.0),
        (-4868.0, centre_y, 1370.0),
        (-4868.0, centre_y + 85.0, 1405.0),
        (-4868.0, next_y, 1510.0),
    ]
    for part in range(4):
        festoon.append(cylinder_between(
            f"40T_FestoonCable_{loop_index:02d}_{part+1}", points[part], points[part+1],
            1.4, dark, bridge_tags_40))

# Trolley-owned electrical cabinet and service beacon follow trolley Y as well
# as bridge X through the native tag discovery.
trolley_tags = ("LB.Motion.CraneTrolley", "LB.Crane.40T", "LB.Module.CraneService")
trolley_service = [
    cube("40T_TrolleyServiceCabinet", (-4890.0, -2000.0, 1615.0),
         (58.0, 72.0, 64.0), dark, trolley_tags),
    cube("40T_TrolleyServiceCabinetFace", (-4859.0, -2000.0, 1615.0),
         (4.0, 62.0, 54.0), yellow, trolley_tags),
]


def identity(label, x, y, z, body, crane_tag, faces_west):
    backing = cube(label + "_Backing", (x, y, z), (5.0, 360.0, 74.0), dark,
                   ("LB.Motion.CraneBridge", crane_tag, "LB.Module.CraneIdentity"))
    text_x = x - 4.0 if faces_west else x + 4.0
    rotation = unreal.Rotator(yaw=180.0 if faces_west else 0.0)
    text = actors.spawn_actor_from_class(
        unreal.TextRenderActor, unreal.Vector(text_x, y, z), rotation)
    text.set_actor_label(PREFIX + label + "_Text")
    text.tags = tags("LB.Motion.CraneBridge", crane_tag, "LB.Module.CraneIdentity",
                     "LB.Asset.Candidate.v031", "LB.Asset.CandidateNotPromoted")
    component = text.text_render
    component.set_editor_properties({
        "text": body,
        "world_size": 18.0,
        "horizontal_alignment": unreal.HorizTextAligment.EHTA_CENTER,
        "vertical_alignment": unreal.VerticalTextAligment.EVRTA_TEXT_CENTER,
        "text_render_color": unreal.Color(232, 236, 226, 255),
        "can_ever_affect_navigation": False,
        "mobility": unreal.ComponentMobility.MOVABLE,
    })
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    return backing, text


identity_40 = identity(
    "40T_WestIdentity", -5228.0, -2415.0, 1505.0,
    "CAIRNWELL AUTOMOTIVE\nCR-40-01  |  SWL 40 t", "LB.Crane.40T", True)
identity_30 = identity(
    "30T_WestIdentity", -8273.0, -2415.0, 1505.0,
    "CAIRNWELL AUTOMOTIVE\nCR-30-01  |  SWL 30 t", "LB.Crane.30T", True)

# Correct the actual sources of clipped luminance. The emergency light was
# directly below the moving coil, while the roof fills were 900–1450 intensity.
light_changes = []
for actor in actors.get_all_level_actors():
    label = actor.get_actor_label()
    light = actor.get_component_by_class(unreal.LightComponent)
    if light is None:
        continue
    if label.startswith("LB_INT_FRONT_FactoryFill_"):
        old = float(light.get_editor_property("intensity"))
        new = 300.0 if label not in {"LB_INT_FRONT_FactoryFill_11", "LB_INT_FRONT_FactoryFill_12"} else 380.0
        light.set_editor_property("intensity", new)
        light_changes.append({"actor": label, "old": old, "new": new})
    elif label == "LB_MOTH_V004_EmergencyPool_02":
        old = float(light.get_editor_property("intensity"))
        light.set_editor_property("intensity", 0.0)
        light_changes.append({"actor": label, "old": old, "new": 0.0})
    elif label == "LB_PR004_V028_CraneServiceFill":
        old = float(light.get_editor_property("intensity"))
        light.set_editor_property("intensity", 0.0)
        light_changes.append({"actor": label, "old": old, "new": 0.0})

# A shadowless camera-side spot provides readable package/hook evidence without
# lighting the underside or the complete ceiling grid.
close_fill = actors.spawn_actor_from_class(
    unreal.SpotLight, unreal.Vector(-5900.0, -850.0, 960.0), unreal.Rotator())
close_fill.set_actor_label(PREFIX + "CHookCameraFill")
close_fill.tags = tags("LB.Lighting.Candidate", "LB.Asset.Candidate.v031", "LB.Asset.CandidateNotPromoted")
close_target = unreal.Vector(-5050.0, -1850.0, 740.0)
close_fill.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
    close_fill.get_actor_location(), close_target), False)
close_fill.spot_light_component.set_editor_properties({
    "intensity": 950.0,
    "attenuation_radius": 2600.0,
    "inner_cone_angle": 35.0,
    "outer_cone_angle": 68.0,
    "source_radius": 65.0,
    "soft_source_radius": 120.0,
    "cast_shadows": False,
    "light_color": unreal.Color(224, 232, 242, 255),
})

# Replace the rejected alignment with a camera between structural column rows.
for actor in list(actors.get_all_level_actors()):
    if actor.get_actor_label().startswith(PREFIX + "CAM_"):
        actors.destroy_actor(actor)


def camera(label, location, target, fov, bias):
    actor = actors.spawn_actor_from_class(
        unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(PREFIX + "CAM_" + label)
    actor.tags = tags("LB.Camera.Validation", "LB.Camera.Fixed.PR004Crane.v031",
                      "LB.Asset.Candidate.v031", "LB.Asset.CandidateNotPromoted")
    actor.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
        actor.get_actor_location(), unreal.Vector(*target)), False)
    component = actor.camera_component
    component.set_editor_properties({
        "field_of_view": fov,
        "aspect_ratio": 16.0 / 9.0,
        "constrain_aspect_ratio": True,
        "post_process_blend_weight": 1.0,
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
    camera("CraneFullSpanWest", (-10150.0, -3000.0, 1080.0),
           (-5050.0, -2415.0, 1460.0), 72.0, -0.85),
    camera("CHookEngagement", (-5900.0, -850.0, 900.0),
           (-5050.0, -1850.0, 730.0), 34.0, -0.25),
    camera("PR004Deposit", (-5850.0, -330.0, 720.0),
           (-5050.0, -2000.0, 170.0), 44.0, -0.50),
]

if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")

payload = {
    "$schema": "line-boss/audit/press-shop-pr004-crane-fabrication-candidate-v031/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "FABRICATION_LIGHTING_AND_CAMERA_REWORK_BUILT__REGATES_REQUIRED__NOT_PROMOTED",
    "base_map": BASE,
    "map": MAP,
    "bridge_material_override_count": len(overridden_bridge_components),
    "splice_plate_count": len(splice_plates),
    "running_rail_count": len(running_rails),
    "festoon_actor_count": len(festoon),
    "trolley_service_actor_count": len(trolley_service),
    "identities": [
        "CAIRNWELL AUTOMOTIVE / CR-40-01 / SWL 40 t",
        "CAIRNWELL AUTOMOTIVE / CR-30-01 / SWL 30 t",
    ],
    "light_changes": light_changes,
    "camera_side_spot_intensity": 950.0,
    "fixed_cameras": [actor.get_actor_label() for actor in cameras],
    "span_cm_unchanged": span,
    "runtime_gate": "OPEN",
    "collision_navigation_gate": "OPEN",
    "visual_gate": "OPEN",
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(
    f"LINE_BOSS_PR004_CRANE_FABRICATION_V031_BUILD_PASS "
    f"splices={len(splice_plates)} festoon={len(festoon)} map={MAP}")
unreal.SystemLibrary.quit_editor()
