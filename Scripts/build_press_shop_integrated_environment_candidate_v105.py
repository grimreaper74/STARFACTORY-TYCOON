"""Build an isolated v107 whole-shop environment/composition successor.

v104 corrected the exact lighting warnings and invalid floor texture but failed
visual review because its cameras were above/inside the roof and the factory was
lit as isolated pools.  v105 preserves v104 and adds only shared hall context:
continuous industrial ceiling light, measured slab joints, logistics-bay
markings, and fixed operational cameras below the roof/crane structure.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_IntegratedEnvironmentCandidate_v104"
MAP = "/Game/LineBoss/Maps/LB_PressShop_IntegratedEnvironmentCandidate_v107"
DEST = "/Game/LineBoss/Candidates/PressShop/IntegratedEnvironment_v107"
OUT = ROOT / "Saved/Audits/PressShopIntegration/integrated_environment_build_v107.json"

library = unreal.EditorAssetLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if library.does_asset_exist(MAP):
    raise RuntimeError(f"refusing to overwrite preserved candidate {MAP}")
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError("could not create isolated v105 from v104")


def make_constant_material(name, colour, roughness=0.78, metallic=0.0, emissive=None):
    material = asset_tools.create_asset(name, DEST + "/Materials", unreal.Material, unreal.MaterialFactoryNew())
    if material is None:
        raise RuntimeError(name)
    colour_node = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -260, -40)
    colour_node.set_editor_property("constant", unreal.LinearColor(*colour, 1.0))
    rough = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -260, 80)
    rough.set_editor_property("r", roughness)
    metal = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -260, 150)
    metal.set_editor_property("r", metallic)
    mel.connect_material_property(colour_node, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    if emissive is not None:
        emission = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -260, 230)
        emission.set_editor_property("constant", unreal.LinearColor(*emissive, 1.0))
        mel.connect_material_property(emission, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(material)
    library.save_loaded_asset(material, only_if_is_dirty=False)
    return material


joint_mat = make_constant_material("M_CA_MW_SlabJoint_v105", (0.035, 0.041, 0.043), 0.92)
route_mat = make_constant_material("M_CA_MW_LogisticsRoute_v105", (0.045, 0.155, 0.115), 0.80)
yellow_mat = make_constant_material("M_CA_MW_RouteYellow_v105", (0.72, 0.47, 0.015), 0.72)
luminaire_mat = make_constant_material(
    "M_CA_MW_LuminaireLens_v105", (0.70, 0.76, 0.78), 0.30, 0.0, (1.15, 1.22, 1.25))

cube = library.load_asset("/Engine/BasicShapes/Cube.Cube")
if cube is None:
    raise RuntimeError("missing engine cube")


def add_mesh(label, location, scale, material, tags):
    actor = actors_api.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(label)
    component = actor.static_mesh_component
    component.set_static_mesh(cube)
    actor.set_actor_scale3d(unreal.Vector(*scale))
    component.set_material(0, material)
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_editor_property("can_ever_affect_navigation", False)
    component.set_editor_property("cast_shadow", False)
    actor.tags = [unreal.Name(value) for value in tags]
    return actor


common_tags = ["LB.Asset.Candidate.v107", "LB.Asset.CandidateNotPromoted", "LB.Environment.SharedHall.v107"]

# 6 m concrete slab grid over the occupied Press Shop band.  Each cube is only
# 18 mm wide and 4 mm high, so these read as saw-cut joints, not floor planks.
slab_joints = []
for x in range(-12600, 4201, 600):
    slab_joints.append(add_mesh(
        f"LB_ENV_V107_SlabJoint_X_{x:+06d}", (x, -2000, 1.2), (0.18, 120.0, 0.04), joint_mat,
        common_tags + ["LB.Environment.Floor.SawCutJoint"]))
for y in range(-5600, 1601, 600):
    slab_joints.append(add_mesh(
        f"LB_ENV_V107_SlabJoint_Y_{y:+06d}", (-4200, y, 1.25), (168.0, 0.18, 0.04), joint_mat,
        common_tags + ["LB.Environment.Floor.SawCutJoint"]))

# A restrained main logistics spine south of the line, with dashed centre marks.
route_parts = [add_mesh(
    "LB_ENV_V107_MainLogisticsSpine", (-4200, 600, 1.4), (168.0, 18.0, 0.045), route_mat,
    common_tags + ["LB.Environment.Route.MainLogisticsSpine"])]
for x in range(-12000, 3601, 800):
    route_parts.append(add_mesh(
        f"LB_ENV_V107_RouteDash_{x:+06d}", (x, 600, 2.0), (3.2, 0.16, 0.03), yellow_mat,
        common_tags + ["LB.Environment.Route.CentreDash"]))

# Continuous two-row industrial ambient lighting across the occupied production
# band.  Local station task lights remain responsible for close process detail.
lights = []
fixtures = []
for row_y in (-3600, -400):
    for x in range(-11800, 3001, 1600):
        index = len(lights) + 1
        fixtures.append(add_mesh(
            f"LB_ENV_V107_Luminaire_{index:02d}", (x, row_y, 1760), (7.0, 0.42, 0.10), luminaire_mat,
            common_tags + ["LB.Environment.Luminaire"] ))
        light = actors_api.spawn_actor_from_class(
            unreal.RectLight, unreal.Vector(x, row_y, 1725), unreal.Rotator(-90.0, 0.0, 0.0))
        light.set_actor_label(f"LB_ENV_V107_AmbientRect_{index:02d}")
        component = light.get_component_by_class(unreal.RectLightComponent)
        component.set_editor_properties({
            "intensity": 6.5,
            "source_width": 1250.0,
            "source_height": 110.0,
            "attenuation_radius": 2050.0,
            "cast_shadows": False,
            "light_color": unreal.Color(214, 225, 228, 255),
        })
        light.tags = [unreal.Name(value) for value in common_tags + ["LB.Environment.Light.ContinuousAmbient"]]
        lights.append(light)


def add_camera(label, location, target, fov):
    camera = actors_api.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    camera.set_actor_label(label)
    camera.set_actor_rotation(
        unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(), unreal.Vector(*target)), False)
    camera.camera_component.set_editor_properties({
        "field_of_view": fov,
        "aspect_ratio": 16.0 / 9.0,
        "constrain_aspect_ratio": True,
    })
    camera.tags = [unreal.Name(value) for value in common_tags + ["LB.Camera.Validation", "LB.Camera.Fixed.IntegratedEnvironment.v107"]]
    return camera


# All cameras are below the 18 m hall roof and below the overhead crane bridge.
# They frame operational zones rather than trying to show the entire empty shell.
cameras = [
    add_camera("LB_ENV_V107_CAM_FrontEndFlow", (-10600, 900, 980), (-7200, -2100, 520), 59.0),
    add_camera("LB_ENV_V107_CAM_CraneCoil", (-10100, -5000, 1180), (-7000, -2100, 780), 57.0),
    add_camera("LB_ENV_V107_CAM_ConnectedLine", (2800, 500, 900), (-1800, -2050, 520), 58.0),
    add_camera("LB_ENV_V107_CAM_PR009PR010", (2750, -4200, 720), (800, -2050, 260), 54.0),
    add_camera("LB_ENV_V107_CAM_LogisticsSpine", (-9000, 1200, 340), (-3000, 500, 120), 62.0),
]

failures = []
if len(slab_joints) != 42:
    failures.append(f"expected 42 slab joints, found {len(slab_joints)}")
if len(lights) != 20 or len(fixtures) != 20:
    failures.append(f"expected 20 luminaires/lights, found {len(fixtures)}/{len(lights)}")
if len(cameras) != 5:
    failures.append(f"expected five fixed cameras, found {len(cameras)}")
if not levels.save_current_level():
    failures.append("could not save isolated v105")
library.save_directory(DEST, only_if_is_dirty=False, recursive=True)

report = {
    "$schema": "cairnwell/audit/press-shop-integrated-environment-build-v107/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__V107_OPERATIONAL_CAMERA_AND_CONTINUOUS_HALL_CONTEXT_BUILT__EARLY_VISUAL_GATE_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__V107_BUILD__NOT_PROMOTED",
    "source_map": BASE,
    "map": MAP,
    "slab_joint_count": len(slab_joints),
    "route_part_count": len(route_parts),
    "luminaire_count": len(fixtures),
    "ambient_light_count": len(lights),
    "fixed_cameras": [camera.get_actor_label() for camera in cameras],
    "accepted_v103_changed": False,
    "station_authority_changed": False,
    "promotion_authorized": False,
    "press_shop_complete": False,
    "failures": failures,
}
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
