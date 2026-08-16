"""Build isolated PR-008 v076 layered materials and diegetic identity from v075."""

import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PR008VisualCleanupCandidate_v075"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR008LayeredMaterialCandidate_v076"
PREFIX = "LB_PR008_V076_"
DEST = "/Game/LineBoss/Stations/Press/PR008/LayeredMaterial_v076"
MAT = DEST + "/Materials"
AUDIT = ROOT / "Saved/Audits/press_shop_pr008_layered_material_candidate_v076.json"
SOURCE_INVENTORY = ROOT / "Saved/Audits/press_shop_pr008_material_bindings_v075.json"

library = unreal.EditorAssetLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
material_editing = unreal.MaterialEditingLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

map_file = ROOT / "Content/LineBoss/Maps/LB_PressShop_PR008LayeredMaterialCandidate_v076.umap"
if not map_file.exists():
    if not library.duplicate_asset(BASE, MAP):
        raise RuntimeError("Could not duplicate v075 to isolated v076")
    if not library.save_asset(MAP, only_if_is_dirty=False):
        raise RuntimeError("Could not save prepared v076 map")
    unreal.log("LINE_BOSS_PR008_V076_PREPARE_PASS__RERUN_FOR_POPULATION")
    unreal.SystemLibrary.quit_editor()
    raise SystemExit

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

for actor in list(actors_api.get_all_level_actors()):
    if actor.get_actor_label().startswith(PREFIX):
        actors_api.destroy_actor(actor)


def layered_material(name, dark, light, metallic, rough_low, rough_high, noise_scale):
    """Create subtle UV-space colour and roughness breakup without texture dependencies."""
    path = f"{MAT}/{name}"
    material = library.load_asset(path) if library.does_asset_exist(path) else asset_tools.create_asset(
        name, MAT, unreal.Material, unreal.MaterialFactoryNew())
    if material is None:
        raise RuntimeError(f"Could not create {path}")
    material_editing.delete_all_material_expressions(material)

    uv = material_editing.create_material_expression(
        material, unreal.MaterialExpressionTextureCoordinate, -900, -50)
    scale = material_editing.create_material_expression(
        material, unreal.MaterialExpressionConstant, -900, 70)
    scale.set_editor_property("r", noise_scale)
    scaled_uv = material_editing.create_material_expression(
        material, unreal.MaterialExpressionMultiply, -700, -40)
    material_editing.connect_material_expressions(uv, "", scaled_uv, "A")
    material_editing.connect_material_expressions(scale, "", scaled_uv, "B")

    noise = material_editing.create_material_expression(
        material, unreal.MaterialExpressionNoise, -500, -30)
    noise.set_editor_properties({
        "quality": 2,
        "levels": 3,
        "output_min": 0.0,
        "output_max": 1.0,
    })
    material_editing.connect_material_expressions(scaled_uv, "", noise, "Position")

    colour_dark = material_editing.create_material_expression(
        material, unreal.MaterialExpressionConstant3Vector, -500, -210)
    colour_dark.set_editor_property("constant", unreal.LinearColor(*dark, 1.0))
    colour_light = material_editing.create_material_expression(
        material, unreal.MaterialExpressionConstant3Vector, -500, -130)
    colour_light.set_editor_property("constant", unreal.LinearColor(*light, 1.0))
    colour_lerp = material_editing.create_material_expression(
        material, unreal.MaterialExpressionLinearInterpolate, -220, -145)
    material_editing.connect_material_expressions(colour_dark, "", colour_lerp, "A")
    material_editing.connect_material_expressions(colour_light, "", colour_lerp, "B")
    material_editing.connect_material_expressions(noise, "", colour_lerp, "Alpha")

    rough_a = material_editing.create_material_expression(
        material, unreal.MaterialExpressionConstant, -230, 70)
    rough_a.set_editor_property("r", rough_low)
    rough_b = material_editing.create_material_expression(
        material, unreal.MaterialExpressionConstant, -230, 145)
    rough_b.set_editor_property("r", rough_high)
    rough_lerp = material_editing.create_material_expression(
        material, unreal.MaterialExpressionLinearInterpolate, 20, 105)
    material_editing.connect_material_expressions(rough_a, "", rough_lerp, "A")
    material_editing.connect_material_expressions(rough_b, "", rough_lerp, "B")
    material_editing.connect_material_expressions(noise, "", rough_lerp, "Alpha")

    metal = material_editing.create_material_expression(
        material, unreal.MaterialExpressionConstant, 20, 205)
    metal.set_editor_property("r", metallic)
    material_editing.connect_material_property(colour_lerp, "", unreal.MaterialProperty.MP_BASE_COLOR)
    material_editing.connect_material_property(rough_lerp, "", unreal.MaterialProperty.MP_ROUGHNESS)
    material_editing.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    material_editing.recompile_material(material)
    library.save_loaded_asset(material, only_if_is_dirty=False)
    return material


materials = {
    "green": layered_material(
        "M_CA_MW_PR008_LayeredCairnwellGreen_v076",
        (0.018, 0.060, 0.052), (0.040, 0.125, 0.105), 0.56, 0.40, 0.59, 7.5),
    "charcoal": layered_material(
        "M_CA_MW_PR008_LayeredFoundryCharcoal_v076",
        (0.009, 0.013, 0.014), (0.032, 0.040, 0.041), 0.64, 0.48, 0.69, 8.5),
    "yellow": layered_material(
        "M_CA_MW_PR008_LayeredSafetyYellow_v076",
        (0.57, 0.285, 0.002), (0.88, 0.55, 0.008), 0.48, 0.38, 0.60, 9.0),
    "steel": layered_material(
        "M_CA_MW_PR008_LayeredWorkedSteel_v076",
        (0.125, 0.150, 0.170), (0.36, 0.405, 0.440), 1.0, 0.23, 0.44, 12.0),
    "light_grey": layered_material(
        "M_CA_MW_PR008_LayeredServiceGrey_v076",
        (0.25, 0.275, 0.270), (0.46, 0.49, 0.475), 0.42, 0.46, 0.65, 7.0),
    "strip": layered_material(
        "M_CA_MW_PR008_BrightStripSteel_v076",
        (0.40, 0.455, 0.495), (0.70, 0.735, 0.760), 1.0, 0.17, 0.32, 18.0),
    "plate": layered_material(
        "M_CA_MW_PR008_IdentityBacking_v076",
        (0.006, 0.010, 0.011), (0.018, 0.032, 0.030), 0.55, 0.34, 0.48, 10.0),
    "joint": layered_material(
        "M_CA_MW_PR008_FloorJoint_v076",
        (0.010, 0.012, 0.012), (0.026, 0.030, 0.029), 0.08, 0.70, 0.88, 6.0),
}

if not SOURCE_INVENTORY.exists():
    raise RuntimeError(f"Missing required v075 source inventory {SOURCE_INVENTORY}")
source_inventory = json.loads(SOURCE_INVENTORY.read_text(encoding="utf-8"))
source_bindings = {
    (row["actor"], slot["index"]): slot["effective_material"]
    for row in source_inventory["actors"]
    for slot in row["materials"]
}


def material_key(material_name, actor_label):
    if actor_label == "LB_PR008_V075_Live_ProcessStrip":
        return "strip"
    if "CairnwellGreen" in material_name:
        return "green"
    if "FoundryCharcoal" in material_name or material_name == "M_LB_StructureSteel":
        return "charcoal"
    if "SafetyYellow" in material_name or material_name == "M_LB_SafetyYellow":
        return "yellow"
    if any(token in material_name for token in ("GroundSteel", "WorkedSteel", "StripSteel")):
        return "steel"
    if any(token in material_name for token in ("LightGrey", "ServiceGrey")):
        return "light_grey"
    return None


eligible = re.compile(r"^LB_PR008_V063_|^LB_PR008_V06[4-9]_SM_|^LB_PR008_V07[0-3]_SM_|^LB_PR008_V075_Live_ProcessStrip$")
overrides = []
override_counts = Counter()
for actor in actors_api.get_all_level_actors():
    label = actor.get_actor_label()
    if not eligible.match(label):
        continue
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    if component is None or component.static_mesh is None:
        continue
    for index in range(component.get_num_materials()):
        current = component.get_material(index)
        if current is None:
            continue
        key = material_key(current.get_name(), label)
        if key is None:
            continue
        component.set_material(index, materials[key])
        override_counts[key] += 1
        overrides.append({
            "actor": label,
            "slot_index": index,
            "source_material": source_bindings.get((label, index), current.get_path_name()),
            "layer": key,
            "candidate_material": materials[key].get_path_name(),
        })

if len(overrides) < 150:
    raise RuntimeError(f"Expected at least 150 controlled material overrides, found {len(overrides)}")


def cube_actor(label, centre, dimensions, material, tags):
    actor = actors_api.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(*centre), unreal.Rotator())
    actor.set_actor_label(PREFIX + label)
    actor.tags = [unreal.Name(value) for value in (
        "LB.Asset.Candidate.v076", "LB.Asset.CandidateNotPromoted", *tags)]
    component = actor.static_mesh_component
    component.set_static_mesh(library.load_asset("/Engine/BasicShapes/Cube.Cube"))
    component.set_world_scale3d(unreal.Vector(
        dimensions[0] / 100.0, dimensions[1] / 100.0, dimensions[2] / 100.0))
    component.set_material(0, material)
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_collision_profile_name(unreal.Name("NoCollision"))
    component.set_editor_property("can_ever_affect_navigation", False)
    return actor


identity_plate = cube_actor(
    "IdentityPlate_PR008_MainPress",
    (-504.0, -2000.0, 218.0),
    (3.0, 132.0, 43.0),
    materials["plate"],
    ("LB.Station.PR008.Identity", "LB.Navigation.Neutral", "LB.Identity.Diegetic"),
)


def identity_text(label, value, location, size, colour):
    actor = actors_api.spawn_actor_from_class(
        unreal.TextRenderActor, unreal.Vector(*location), unreal.Rotator(yaw=180.0))
    actor.set_actor_label(PREFIX + "TEXT_" + label)
    actor.tags = [unreal.Name(value) for value in (
        "LB.Asset.Candidate.v076", "LB.Asset.CandidateNotPromoted",
        "LB.Station.PR008.Identity", "LB.Identity.Diegetic")]
    component = actor.text_render
    component.set_text(value)
    component.set_world_size(size)
    component.set_text_render_color(colour)
    component.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER)
    component.set_vertical_alignment(unreal.VerticalTextAligment.EVRTA_TEXT_CENTER)
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_editor_property("can_ever_affect_navigation", False)
    return actor


identity = [
    identity_text("Corporation", "CAIRNWELL AUTOMOTIVE", (-505.7, -2000.0, 230.0), 4.3,
                  unreal.Color(58, 184, 139, 255)),
    identity_text("Site", "MOORCROSS WORKS", (-505.7, -2000.0, 219.0), 3.7,
                  unreal.Color(214, 221, 216, 255)),
    identity_text("Station", "PR-008  SERVO BLANKING LINE", (-505.7, -2000.0, 208.0), 3.7,
                  unreal.Color(242, 195, 0, 255)),
]

# Restrained authored expansion joints break up the otherwise monolithic pad.
floor_joints = []
for index, x in enumerate((-900.0, -700.0, -500.0, -300.0, -100.0), start=1):
    floor_joints.append(cube_actor(
        f"FloorJoint_{index:02d}", (x, -1995.0, 5.76), (1.6, 602.0, 0.18),
        materials["joint"], ("LB.Floor.PR008.FoundationJoint", "LB.Navigation.Neutral")))

# Duplicate the v075 views so every v076 capture uses candidate-versioned cameras.
camera_specs = [
    ("CleanProcess", (-1510.0, -3040.0, 690.0), (-520.0, -1995.0, 130.0), 56.0),
    ("CleanMotion", (-930.0, -1450.0, 410.0), (-500.0, -1995.0, 115.0), 50.0),
    ("CleanHMI", (-405.0, -2600.0, 185.0), (-185.0, -2255.0, 132.0), 34.0),
    ("ClearPR009Interface", (360.0, -1450.0, 360.0), (-70.0, -1995.0, 105.0), 45.0),
]
cameras = []
for label, location, target, fov in camera_specs:
    actor = actors_api.spawn_actor_from_class(
        unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(PREFIX + "CAM_" + label)
    actor.tags = [unreal.Name(value) for value in (
        "LB.Camera.Validation", "LB.Camera.Fixed.PR008.v076", "LB.Asset.CandidateNotPromoted")]
    actor.set_actor_rotation(
        unreal.MathLibrary.find_look_at_rotation(actor.get_actor_location(), unreal.Vector(*target)), False)
    actor.camera_component.set_editor_properties({
        "field_of_view": fov,
        "aspect_ratio": 16.0 / 9.0,
        "constrain_aspect_ratio": True,
    })
    cameras.append(actor)

column = next(
    (actor for actor in actors_api.get_all_level_actors()
     if actor.get_actor_label() == "LB_PRESS_Column_0_-2250"), None)
if column is None or column.get_editor_property("hidden"):
    raise RuntimeError("The genuine hall column must remain present in v076")

if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")
library.save_directory(DEST, only_if_is_dirty=False, recursive=True)

payload = {
    "$schema": "line-boss/audit/press-shop-pr008-layered-material-candidate-v076/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PR008_LAYERED_MATERIAL_IDENTITY_AND_FOUNDATION_DETAIL_BUILT__ALL_GATES_AND_FRESH_VISUAL_REVIEW_REQUIRED__NOT_PROMOTED",
    "map": MAP,
    "base_map": BASE,
    "eligible_actor_pattern": eligible.pattern,
    "material_override_count": len(overrides),
    "material_override_counts": dict(sorted(override_counts.items())),
    "materials": {key: value.get_path_name() for key, value in materials.items()},
    "overrides": overrides,
    "preserved_material_families": [
        "Galvanised", "SensorGlass", "Rubber", "LabelPlate", "DriveBlue", "EStopRed"],
    "identity_plate": identity_plate.get_actor_label(),
    "identity_text": [str(actor.text_render.text) for actor in identity],
    "diegetic_branding": {
        "corporation": "Cairnwell Automotive",
        "site": "Moorcross Works",
        "station": "PR-008 Servo Blanking Line",
        "line_boss_in_world": False,
    },
    "floor_joint_count": len(floor_joints),
    "new_dressing_collision": "NoCollision",
    "new_dressing_navigation": "neutral",
    "fixed_hall_column_preserved": column.get_actor_label(),
    "fixed_cameras": [actor.get_actor_label() for actor in cameras],
    "accepted_pr004_v006_preserved": True,
    "rejected_pr004_v007_v010_unchanged": True,
    "promotion_authorized": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(
    f"LINE_BOSS_PR008_V076_LAYERED_BUILD_PASS overrides={len(overrides)} "
    f"identity={len(identity)} joints={len(floor_joints)} cameras={len(cameras)}"
)
unreal.SystemLibrary.quit_editor()
