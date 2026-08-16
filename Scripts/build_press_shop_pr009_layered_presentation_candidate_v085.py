"""Build isolated PR-009 v085 layered-material/presentation candidate from v084."""

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PR009CorrectedIntegrationCandidate_v084"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR009LayeredPresentationCandidate_v085"
OLD_PREFIX = "LB_PR009_V084_"
PREFIX = "LB_PR009_V085_"
DEST = "/Game/LineBoss/Stations/Press/PR009/Presentation_v085"
MAT = DEST + "/Materials"
OUT = ROOT / "Saved/Audits/press_shop_pr009_layered_presentation_candidate_v085.json"

library = unreal.EditorAssetLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

map_file = ROOT / "Content/LineBoss/Maps/LB_PressShop_PR009LayeredPresentationCandidate_v085.umap"
if not map_file.exists():
    if not library.duplicate_asset(BASE, MAP):
        raise RuntimeError("Could not duplicate isolated PR-009 v084 to v085")
    if not library.save_asset(MAP, only_if_is_dirty=False):
        raise RuntimeError("Could not save prepared PR-009 v085 map")
    unreal.log("CAIRNWELL_PR009_V085_PREPARE_PASS__RERUN_FOR_POPULATION")
    unreal.SystemLibrary.quit_editor()
    raise SystemExit

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

# Remove only inherited v084 review dressing. Core actors are retained and relabelled.
for actor in list(actors_api.get_all_level_actors()):
    label = actor.get_actor_label()
    if label.startswith(OLD_PREFIX + "CAM_") or label.startswith(OLD_PREFIX + "TEXT_"):
        actors_api.destroy_actor(actor)
for actor in actors_api.get_all_level_actors():
    label = actor.get_actor_label()
    if label.startswith(OLD_PREFIX):
        actor.set_actor_label(PREFIX + label[len(OLD_PREFIX):])
        tags = [str(tag) for tag in actor.tags if str(tag) != "LB.Asset.Candidate.v084"]
        tags.extend(("LB.Asset.Candidate.v085", "LB.Asset.CandidateNotPromoted"))
        actor.tags = [unreal.Name(tag) for tag in dict.fromkeys(tags)]

# Clear only this candidate's previously spawned dressing on safe reruns.
for actor in list(actors_api.get_all_level_actors()):
    if actor.get_actor_label().startswith(PREFIX + "PRESENT_"):
        actors_api.destroy_actor(actor)


def layered_surface(name, face, edge, metallic, face_roughness, edge_roughness, edge_strength,
                    emissive=None):
    """Smooth layered response without the rejected coarse procedural grain."""
    path = f"{MAT}/{name}"
    material = library.load_asset(path) if library.does_asset_exist(path) else asset_tools.create_asset(
        name, MAT, unreal.Material, unreal.MaterialFactoryNew())
    if material is None:
        raise RuntimeError(f"Could not create {path}")
    mel.delete_all_material_expressions(material)

    face_node = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -520, -150)
    face_node.set_editor_property("constant", unreal.LinearColor(*face, 1.0))
    edge_node = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -520, -65)
    edge_node.set_editor_property("constant", unreal.LinearColor(*edge, 1.0))
    fresnel = mel.create_material_expression(material, unreal.MaterialExpressionFresnel, -520, 55)
    strength = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -520, 165)
    strength.set_editor_property("r", edge_strength)
    edge_alpha = mel.create_material_expression(material, unreal.MaterialExpressionMultiply, -305, 75)
    mel.connect_material_expressions(fresnel, "", edge_alpha, "A")
    mel.connect_material_expressions(strength, "", edge_alpha, "B")
    colour = mel.create_material_expression(material, unreal.MaterialExpressionLinearInterpolate, -90, -85)
    mel.connect_material_expressions(face_node, "", colour, "A")
    mel.connect_material_expressions(edge_node, "", colour, "B")
    mel.connect_material_expressions(edge_alpha, "", colour, "Alpha")

    rough_face = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -305, 205)
    rough_face.set_editor_property("r", face_roughness)
    rough_edge = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -305, 280)
    rough_edge.set_editor_property("r", edge_roughness)
    rough = mel.create_material_expression(material, unreal.MaterialExpressionLinearInterpolate, -90, 240)
    mel.connect_material_expressions(rough_face, "", rough, "A")
    mel.connect_material_expressions(rough_edge, "", rough, "B")
    mel.connect_material_expressions(fresnel, "", rough, "Alpha")
    metal = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -90, 345)
    metal.set_editor_property("r", metallic)

    mel.connect_material_property(colour, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    if emissive is not None:
        emit = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -90, 430)
        emit.set_editor_property("constant", unreal.LinearColor(*emissive, 1.0))
        mel.connect_material_property(emit, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(material)
    library.save_loaded_asset(material, only_if_is_dirty=False)
    return material


materials = {
    "frame": layered_surface("M_CA_MW_PR009_LayeredFoundryCharcoal_v085",
        (0.018, 0.025, 0.026), (0.070, 0.088, 0.086), 0.58, 0.54, 0.34, 0.15),
    "green": layered_surface("M_CA_MW_PR009_LayeredCairnwellGreen_v085",
        (0.025, 0.105, 0.084), (0.065, 0.205, 0.165), 0.50, 0.46, 0.31, 0.13),
    "yellow": layered_surface("M_CA_MW_PR009_LayeredSafetyYellow_v085",
        (0.54, 0.285, 0.003), (0.82, 0.50, 0.012), 0.38, 0.52, 0.34, 0.10),
    "light_grey": layered_surface("M_CA_MW_PR009_LayeredServiceGrey_v085",
        (0.27, 0.295, 0.285), (0.43, 0.46, 0.44), 0.30, 0.58, 0.40, 0.09),
    "steel": layered_surface("M_CA_MW_PR009_StructuralSteel_v085",
        (0.105, 0.125, 0.135), (0.28, 0.32, 0.34), 0.92, 0.40, 0.25, 0.22),
    "machined": layered_surface("M_CA_MW_PR009_MachinedSteel_v085",
        (0.36, 0.405, 0.435), (0.68, 0.72, 0.75), 1.0, 0.20, 0.12, 0.34),
    "blank": layered_surface("M_CA_MW_PR009_OiledBlankSteel_v085",
        (0.44, 0.49, 0.52), (0.76, 0.80, 0.82), 1.0, 0.23, 0.11, 0.40),
    "galv": layered_surface("M_CA_MW_PR009_GalvanisedMesh_v085",
        (0.30, 0.34, 0.35), (0.63, 0.67, 0.68), 0.88, 0.44, 0.27, 0.24),
    "rubber": layered_surface("M_CA_MW_PR009_Rubber_v085",
        (0.008, 0.010, 0.010), (0.020, 0.024, 0.023), 0.02, 0.82, 0.70, 0.04),
    "glass": layered_surface("M_CA_MW_PR009_SensorGlass_v085",
        (0.004, 0.020, 0.024), (0.010, 0.075, 0.080), 0.08, 0.16, 0.09, 0.11,
        emissive=(0.0, 0.015, 0.018)),
    "screen": layered_surface("M_CA_MW_PR009_HMIScreenOnline_v085",
        (0.003, 0.020, 0.017), (0.010, 0.085, 0.060), 0.04, 0.18, 0.10, 0.08,
        emissive=(0.015, 1.40, 0.68)),
    "red": layered_surface("M_CA_MW_PR009_EStopRed_v085",
        (0.42, 0.003, 0.002), (0.85, 0.025, 0.015), 0.22, 0.34, 0.20, 0.13),
    "amber": layered_surface("M_CA_MW_PR009_AmberSafetyActive_v085",
        (0.58, 0.16, 0.002), (0.95, 0.42, 0.008), 0.10, 0.30, 0.18, 0.10,
        emissive=(2.40, 0.42, 0.005)),
    "white": layered_surface("M_CA_MW_PR009_LabelWhite_v085",
        (0.52, 0.56, 0.54), (0.72, 0.75, 0.72), 0.08, 0.62, 0.45, 0.06),
    "blue": layered_surface("M_CA_MW_PR009_DriveBlue_v085",
        (0.015, 0.12, 0.19), (0.04, 0.29, 0.42), 0.48, 0.42, 0.27, 0.12),
}


def role_for(slot_name):
    value = slot_name.upper().replace("-", "_")
    # Order is deliberate: explicit authored PR-009 roles override generic tokens.
    for token, role in (
        ("PR009_BLANK", "blank"), ("PR009_MACHINED", "machined"),
        ("PR009_LIGHT_GREY", "light_grey"), ("PR009_SCREEN", "screen"),
        ("PR009_AMBER", "amber"), ("PR009_YELLOW", "yellow"),
        ("PR009_GREEN", "green"), ("PR009_GALV", "galv"),
        ("PR009_GLASS", "glass"), ("PR009_RUBBER", "rubber"),
        ("PR009_STEEL", "steel"), ("PR009_FRAME", "frame"),
        ("PR009_RED", "red"), ("PR009_WHITE", "white"),
        ("GROUNDSTEEL", "machined"), ("GALVANISED", "galv"),
        ("CAIRNWELLGREEN", "green"), ("SAFETYYELLOW", "yellow"),
        ("SENSORGLASS", "glass"), ("ESTOPRED", "red"),
        ("DRIVEBLUE", "blue"), ("LABELPLATE", "white"),
        ("FOUNDRYCHARCOAL", "frame"),
    ):
        if token in value:
            return role
    return "frame"


override_counts = Counter()
slot_role_counts = Counter()
overrides = []
for actor in actors_api.get_all_level_actors():
    label = actor.get_actor_label()
    if not label.startswith(PREFIX) or not isinstance(actor, unreal.StaticMeshActor):
        continue
    component = actor.static_mesh_component
    mesh = component.static_mesh
    if not mesh:
        continue
    for index, slot in enumerate(mesh.get_editor_property("static_materials")):
        slot_name = str(slot.get_editor_property("imported_material_slot_name") or
                        slot.get_editor_property("material_slot_name"))
        role = role_for(slot_name)
        component.set_material(index, materials[role])
        override_counts[role] += 1
        slot_role_counts[f"{slot_name} -> {role}"] += 1
        overrides.append({"actor": label, "slot_index": index, "slot": slot_name, "role": role})
if len(overrides) < 230:
    raise RuntimeError(f"Expected at least 230 PR-009 material overrides, found {len(overrides)}")


def cube(label, centre, dimensions, material, tags):
    actor = actors_api.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*centre), unreal.Rotator())
    if actor is None:
        raise RuntimeError(f"Could not spawn {label}")
    actor.set_actor_label(PREFIX + "PRESENT_" + label)
    actor.tags = [unreal.Name(tag) for tag in (
        "LB.Asset.Candidate.v085", "LB.Asset.CandidateNotPromoted", *tags)]
    component = actor.static_mesh_component
    component.set_static_mesh(library.load_asset("/Engine/BasicShapes/Cube.Cube"))
    component.set_world_scale3d(unreal.Vector(
        dimensions[0] / 100.0, dimensions[1] / 100.0, dimensions[2] / 100.0))
    component.set_material(0, material)
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_collision_profile_name(unreal.Name("NoCollision"))
    component.set_editor_property("can_ever_affect_navigation", False)
    return actor


identity_plate = cube("IdentityPlate", (600.0, -2264.0, 202.0), (210.0, 3.0, 58.0), materials["frame"],
                      ("LB.Identity.CairnwellMoorcross", "LB.Navigation.Neutral"))


def text_actor(label, value, location, size, colour):
    actor = actors_api.spawn_actor_from_class(unreal.TextRenderActor, unreal.Vector(*location), unreal.Rotator(yaw=90.0))
    actor.set_actor_label(PREFIX + "PRESENT_TEXT_" + label)
    actor.tags = [unreal.Name(tag) for tag in (
        "LB.Asset.Candidate.v085", "LB.Asset.CandidateNotPromoted", "LB.Identity.CairnwellMoorcross")]
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
    text_actor("Corporation", "CAIRNWELL AUTOMOTIVE", (600.0, -2266.0, 217.0), 6.0,
               unreal.Color(70, 220, 165, 255)),
    text_actor("Site", "MOORCROSS WORKS", (600.0, -2266.0, 202.0), 5.2,
               unreal.Color(228, 235, 230, 255)),
    text_actor("Station", "PR-009  AUTOMATED BLANK STACKER", (600.0, -2266.0, 187.0), 4.5,
               unreal.Color(242, 195, 0, 255)),
]

# Restrained local light/reflection support; inherited calibrated v079 hall lighting remains authoritative.
lights = []
for label, x in (("West", 360.0), ("East", 840.0)):
    light = actors_api.spawn_actor_from_class(unreal.RectLight, unreal.Vector(x, -2000.0, 820.0), unreal.Rotator())
    light.set_actor_label(PREFIX + "PRESENT_LIGHT_" + label)
    light.tags = [unreal.Name("LB.Asset.Candidate.v085"), unreal.Name("LB.Asset.CandidateNotPromoted"),
                  unreal.Name("LB.Lighting.PR009.Calibrated")]
    light.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
        light.get_actor_location(), unreal.Vector(x, -2000.0, 100.0)), False)
    light.rect_light_component.set_editor_properties({
        "intensity": 300.0, "attenuation_radius": 1000.0,
        "source_width": 210.0, "source_height": 36.0,
        "light_color": unreal.Color(220, 234, 240, 255),
        "cast_shadows": True, "affect_global_illumination": True, "affect_reflection": True,
    })
    lights.append(light)

reflection = actors_api.spawn_actor_from_class(
    unreal.SphereReflectionCapture, unreal.Vector(600.0, -2000.0, 175.0), unreal.Rotator())
reflection.set_actor_label(PREFIX + "PRESENT_Reflection_LocalMachine")
reflection.tags = [unreal.Name("LB.Asset.Candidate.v085"), unreal.Name("LB.Asset.CandidateNotPromoted"),
                   unreal.Name("LB.Reflection.PR009.Local")]
reflection.capture_component.set_editor_properties({
    "influence_radius": 900.0, "brightness": 0.72, "runtime_capture": True,
    "reflection_source_type": unreal.ReflectionSourceType.CAPTURED_SCENE,
    "runtime_skylight_scale": unreal.LinearColor(0.055, 0.070, 0.078, 1.0),
})


def camera(label, location, target, fov):
    actor = actors_api.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(PREFIX + "PRESENT_CAM_" + label)
    actor.tags = [unreal.Name("LB.Camera.Validation"), unreal.Name("LB.Camera.Fixed.PR009.v085"),
                  unreal.Name("LB.Asset.CandidateNotPromoted")]
    actor.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
        actor.get_actor_location(), unreal.Vector(*target)), False)
    actor.camera_component.set_editor_properties({
        "field_of_view": fov, "aspect_ratio": 16.0 / 9.0, "constrain_aspect_ratio": True})
    return actor


cameras = [
    camera("Process", (-590, -1220, 565), (285, -2000, 130), 50),
    camera("Interface", (-180, -1390, 325), (145, -2000, 108), 41),
    camera("CellHero", (1190, -1260, 520), (600, -2000, 150), 47),
    camera("Elevated", (310, -1090, 820), (510, -2000, 135), 53),
]

if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")
library.save_directory(DEST, only_if_is_dirty=False, recursive=True)

payload = {
    "$schema": "cairnwell/audit/press-shop-pr009-layered-presentation-candidate-v085/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PR009_V085_EXPLICIT_AUTHORED_ROLE_LAYERED_MATERIAL_IDENTITY_AND_CALIBRATED_PRESENTATION_BUILD_PASS__ALL_RUNTIME_AND_FRESH_VISUAL_GATES_REQUIRED__NOT_PROMOTED",
    "map": MAP,
    "base_map": BASE,
    "rejected_visual_predecessor": "/Game/LineBoss/Maps/LB_PressShop_PR009CorrectedIntegrationCandidate_v084",
    "material_strategy": "explicit authored PR-009 slot roles with smooth face/edge layering; no rejected coarse procedural grain",
    "material_override_count": len(overrides),
    "material_override_counts": dict(sorted(override_counts.items())),
    "slot_role_counts": dict(sorted(slot_role_counts.items())),
    "materials": {key: value.get_path_name() for key, value in materials.items()},
    "identity_plate": identity_plate.get_actor_label(),
    "identity_text": [str(actor.text_render.text) for actor in identity],
    "line_boss_in_world": False,
    "local_light_count": len(lights),
    "reflection_capture": reflection.get_actor_label(),
    "fixed_cameras": [actor.get_actor_label() for actor in cameras],
    "new_dressing_collision": "NoCollision",
    "new_dressing_navigation": "neutral",
    "accepted_pr004_v006_preserved": True,
    "rejected_pr004_v007_v010_unchanged": True,
    "pr010_started": False,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
unreal.log(payload["status"])
unreal.SystemLibrary.quit_editor()
