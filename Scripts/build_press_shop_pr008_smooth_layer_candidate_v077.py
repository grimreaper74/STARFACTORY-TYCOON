"""Build isolated PR-008 v077 smooth powder-coat/steel correction from retained v075."""

import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PR008VisualCleanupCandidate_v075"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR008SmoothLayerCandidate_v077"
PREFIX = "LB_PR008_V077_"
DEST = "/Game/LineBoss/Stations/Press/PR008/SmoothLayer_v077"
MAT = DEST + "/Materials"
AUDIT = ROOT / "Saved/Audits/press_shop_pr008_smooth_layer_candidate_v077.json"
SOURCE_INVENTORY = ROOT / "Saved/Audits/press_shop_pr008_material_bindings_v075.json"

library = unreal.EditorAssetLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
material_editing = unreal.MaterialEditingLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

map_file = ROOT / "Content/LineBoss/Maps/LB_PressShop_PR008SmoothLayerCandidate_v077.umap"
if not map_file.exists():
    if not library.duplicate_asset(BASE, MAP):
        raise RuntimeError("Could not duplicate retained v075 to isolated v077")
    if not library.save_asset(MAP, only_if_is_dirty=False):
        raise RuntimeError("Could not save prepared v077 map")
    unreal.log("LINE_BOSS_PR008_V077_PREPARE_PASS__RERUN_FOR_POPULATION")
    unreal.SystemLibrary.quit_editor()
    raise SystemExit

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

for actor in list(actors_api.get_all_level_actors()):
    if actor.get_actor_label().startswith(PREFIX):
        actors_api.destroy_actor(actor)


def smooth_surface(name, face, edge, metallic, face_roughness, edge_roughness, edge_strength):
    """Create smooth powder-coat/metal layering with restrained view-edge response."""
    path = f"{MAT}/{name}"
    material = library.load_asset(path) if library.does_asset_exist(path) else asset_tools.create_asset(
        name, MAT, unreal.Material, unreal.MaterialFactoryNew())
    if material is None:
        raise RuntimeError(f"Could not create {path}")
    material_editing.delete_all_material_expressions(material)

    face_colour = material_editing.create_material_expression(
        material, unreal.MaterialExpressionConstant3Vector, -520, -140)
    face_colour.set_editor_property("constant", unreal.LinearColor(*face, 1.0))
    edge_colour = material_editing.create_material_expression(
        material, unreal.MaterialExpressionConstant3Vector, -520, -55)
    edge_colour.set_editor_property("constant", unreal.LinearColor(*edge, 1.0))
    fresnel = material_editing.create_material_expression(
        material, unreal.MaterialExpressionFresnel, -520, 80)
    strength = material_editing.create_material_expression(
        material, unreal.MaterialExpressionConstant, -520, 185)
    strength.set_editor_property("r", edge_strength)
    edge_alpha = material_editing.create_material_expression(
        material, unreal.MaterialExpressionMultiply, -315, 95)
    material_editing.connect_material_expressions(fresnel, "", edge_alpha, "A")
    material_editing.connect_material_expressions(strength, "", edge_alpha, "B")

    colour_lerp = material_editing.create_material_expression(
        material, unreal.MaterialExpressionLinearInterpolate, -90, -75)
    material_editing.connect_material_expressions(face_colour, "", colour_lerp, "A")
    material_editing.connect_material_expressions(edge_colour, "", colour_lerp, "B")
    material_editing.connect_material_expressions(edge_alpha, "", colour_lerp, "Alpha")

    rough_face = material_editing.create_material_expression(
        material, unreal.MaterialExpressionConstant, -315, 210)
    rough_face.set_editor_property("r", face_roughness)
    rough_edge = material_editing.create_material_expression(
        material, unreal.MaterialExpressionConstant, -315, 285)
    rough_edge.set_editor_property("r", edge_roughness)
    rough_lerp = material_editing.create_material_expression(
        material, unreal.MaterialExpressionLinearInterpolate, -90, 245)
    material_editing.connect_material_expressions(rough_face, "", rough_lerp, "A")
    material_editing.connect_material_expressions(rough_edge, "", rough_lerp, "B")
    material_editing.connect_material_expressions(fresnel, "", rough_lerp, "Alpha")

    metal = material_editing.create_material_expression(
        material, unreal.MaterialExpressionConstant, -90, 345)
    metal.set_editor_property("r", metallic)
    material_editing.connect_material_property(colour_lerp, "", unreal.MaterialProperty.MP_BASE_COLOR)
    material_editing.connect_material_property(rough_lerp, "", unreal.MaterialProperty.MP_ROUGHNESS)
    material_editing.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    material_editing.recompile_material(material)
    library.save_loaded_asset(material, only_if_is_dirty=False)
    return material


materials = {
    "green": smooth_surface(
        "M_CA_MW_PR008_SmoothCairnwellGreen_v077",
        (0.022, 0.075, 0.064), (0.050, 0.145, 0.122), 0.52, 0.47, 0.34, 0.13),
    "charcoal": smooth_surface(
        "M_CA_MW_PR008_SmoothFoundryCharcoal_v077",
        (0.012, 0.017, 0.018), (0.043, 0.052, 0.052), 0.60, 0.58, 0.40, 0.12),
    "yellow": smooth_surface(
        "M_CA_MW_PR008_SmoothSafetyYellow_v077",
        (0.70, 0.39, 0.004), (0.94, 0.66, 0.018), 0.42, 0.48, 0.34, 0.10),
    "steel": smooth_surface(
        "M_CA_MW_PR008_SmoothWorkedSteel_v077",
        (0.30, 0.345, 0.380), (0.62, 0.665, 0.700), 1.0, 0.28, 0.18, 0.36),
    "light_grey": smooth_surface(
        "M_CA_MW_PR008_SmoothServiceGrey_v077",
        (0.32, 0.35, 0.34), (0.50, 0.53, 0.51), 0.36, 0.56, 0.39, 0.10),
    "strip": smooth_surface(
        "M_CA_MW_PR008_BrightStripSteel_v077",
        (0.54, 0.59, 0.63), (0.82, 0.85, 0.87), 1.0, 0.20, 0.12, 0.42),
    "plate": smooth_surface(
        "M_CA_MW_PR008_IdentityBacking_v077",
        (0.005, 0.010, 0.010), (0.024, 0.055, 0.047), 0.48, 0.42, 0.28, 0.12),
    "joint": smooth_surface(
        "M_CA_MW_PR008_FloorJoint_v077",
        (0.010, 0.012, 0.012), (0.020, 0.023, 0.022), 0.05, 0.82, 0.70, 0.05),
}

source_inventory = json.loads(SOURCE_INVENTORY.read_text(encoding="utf-8"))
source_bindings = {
    (row["actor"], slot["index"]): slot["effective_material"]
    for row in source_inventory["actors"] for slot in row["materials"]
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


eligible = re.compile(
    r"^LB_PR008_V063_|^LB_PR008_V06[4-9]_SM_|^LB_PR008_V07[0-3]_SM_|^LB_PR008_V075_Live_ProcessStrip$")
overrides = []
counts = Counter()
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
        counts[key] += 1
        overrides.append({
            "actor": label,
            "slot_index": index,
            "source_material": source_bindings.get((label, index), current.get_path_name()),
            "layer": key,
            "candidate_material": materials[key].get_path_name(),
        })
if len(overrides) < 150:
    raise RuntimeError(f"Expected at least 150 controlled overrides, found {len(overrides)}")


def cube_actor(label, centre, dimensions, material, tags):
    actor = actors_api.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(*centre), unreal.Rotator())
    actor.set_actor_label(PREFIX + label)
    actor.tags = [unreal.Name(value) for value in (
        "LB.Asset.Candidate.v077", "LB.Asset.CandidateNotPromoted", *tags)]
    component = actor.static_mesh_component
    component.set_static_mesh(library.load_asset("/Engine/BasicShapes/Cube.Cube"))
    component.set_world_scale3d(unreal.Vector(
        dimensions[0] / 100.0, dimensions[1] / 100.0, dimensions[2] / 100.0))
    component.set_material(0, material)
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_collision_profile_name(unreal.Name("NoCollision"))
    component.set_editor_property("can_ever_affect_navigation", False)
    return actor


plate = cube_actor(
    "IdentityPlate_PR008_MainPress", (-504.0, -2000.0, 218.0), (3.0, 150.0, 48.0),
    materials["plate"], ("LB.Station.PR008.Identity", "LB.Navigation.Neutral", "LB.Identity.Diegetic"))


def identity_text(label, value, location, size, colour):
    actor = actors_api.spawn_actor_from_class(
        unreal.TextRenderActor, unreal.Vector(*location), unreal.Rotator(yaw=180.0))
    actor.set_actor_label(PREFIX + "TEXT_" + label)
    actor.tags = [unreal.Name(value) for value in (
        "LB.Asset.Candidate.v077", "LB.Asset.CandidateNotPromoted",
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
    identity_text("Corporation", "CAIRNWELL AUTOMOTIVE", (-505.7, -2000.0, 231.5), 5.8,
                  unreal.Color(75, 214, 160, 255)),
    identity_text("Site", "MOORCROSS WORKS", (-505.7, -2000.0, 218.5), 5.0,
                  unreal.Color(225, 231, 227, 255)),
    identity_text("Station", "PR-008  SERVO BLANKING", (-505.7, -2000.0, 206.0), 4.8,
                  unreal.Color(242, 195, 0, 255)),
]

floor_joints = [
    cube_actor(f"FloorJoint_{index:02d}", (x, -1995.0, 5.76), (1.6, 602.0, 0.18),
               materials["joint"], ("LB.Floor.PR008.FoundationJoint", "LB.Navigation.Neutral"))
    for index, x in enumerate((-900.0, -700.0, -500.0, -300.0, -100.0), start=1)
]

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
        "LB.Camera.Validation", "LB.Camera.Fixed.PR008.v077", "LB.Asset.CandidateNotPromoted")]
    actor.set_actor_rotation(
        unreal.MathLibrary.find_look_at_rotation(actor.get_actor_location(), unreal.Vector(*target)), False)
    actor.camera_component.set_editor_properties({
        "field_of_view": fov, "aspect_ratio": 16.0 / 9.0, "constrain_aspect_ratio": True})
    cameras.append(actor)

column = next((actor for actor in actors_api.get_all_level_actors()
               if actor.get_actor_label() == "LB_PRESS_Column_0_-2250"), None)
if column is None or column.get_editor_property("hidden"):
    raise RuntimeError("The genuine hall column must remain present in v077")

if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")
library.save_directory(DEST, only_if_is_dirty=False, recursive=True)

payload = {
    "$schema": "line-boss/audit/press-shop-pr008-smooth-layer-candidate-v077/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "SMOOTH_POWDER_COAT_STEEL_IDENTITY_CORRECTION_BUILT_FROM_RETAINED_V075__ALL_GATES_AND_FRESH_VISUAL_REVIEW_REQUIRED__NOT_PROMOTED",
    "map": MAP,
    "base_map": BASE,
    "rejected_predecessor": "/Game/LineBoss/Maps/LB_PressShop_PR008LayeredMaterialCandidate_v076",
    "material_strategy": "smooth constant face layer plus restrained Fresnel edge response; no procedural grain",
    "material_override_count": len(overrides),
    "material_override_counts": dict(sorted(counts.items())),
    "materials": {key: value.get_path_name() for key, value in materials.items()},
    "overrides": overrides,
    "preserved_material_families": [
        "Galvanised", "SensorGlass", "Rubber", "LabelPlate", "DriveBlue", "EStopRed"],
    "identity_plate": plate.get_actor_label(),
    "identity_text": [str(actor.text_render.text) for actor in identity],
    "line_boss_in_world": False,
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
    f"LINE_BOSS_PR008_V077_SMOOTH_LAYER_BUILD_PASS overrides={len(overrides)} "
    f"identity={len(identity)} joints={len(floor_joints)} cameras={len(cameras)}")
unreal.SystemLibrary.quit_editor()
