"""Build an isolated PR-008 v078 local lighting/reflection environment from retained v077."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PR008SmoothLayerCandidate_v077"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR008ReflectionEnvironmentCandidate_v078"
PREFIX = "LB_PR008_V078_"
DEST = "/Game/LineBoss/Stations/Press/PR008/Environment_v078"
AUDIT = ROOT / "Saved/Audits/press_shop_pr008_reflection_environment_candidate_v078.json"

library = unreal.EditorAssetLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
material_editing = unreal.MaterialEditingLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

map_file = ROOT / "Content/LineBoss/Maps/LB_PressShop_PR008ReflectionEnvironmentCandidate_v078.umap"
if not map_file.exists():
    if not library.duplicate_asset(BASE, MAP):
        raise RuntimeError("Could not duplicate retained v077 to isolated v078")
    if not library.save_asset(MAP, only_if_is_dirty=False):
        raise RuntimeError("Could not save prepared v078 map")
    unreal.log("LINE_BOSS_PR008_V078_PREPARE_PASS__RERUN_FOR_POPULATION")
    unreal.SystemLibrary.quit_editor()
    raise SystemExit

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

for actor in list(actors.get_all_level_actors()):
    if actor.get_actor_label().startswith(PREFIX):
        actors.destroy_actor(actor)


def simple_material(name, base_colour, roughness, emissive_colour=None):
    path = f"{DEST}/{name}"
    material = library.load_asset(path) if library.does_asset_exist(path) else asset_tools.create_asset(
        name, DEST, unreal.Material, unreal.MaterialFactoryNew())
    if material is None:
        raise RuntimeError(f"Could not create {path}")
    material_editing.delete_all_material_expressions(material)
    base = material_editing.create_material_expression(
        material, unreal.MaterialExpressionConstant3Vector, -320, -80)
    base.set_editor_property("constant", unreal.LinearColor(*base_colour, 1.0))
    rough = material_editing.create_material_expression(
        material, unreal.MaterialExpressionConstant, -320, 40)
    rough.set_editor_property("r", roughness)
    material_editing.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    material_editing.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    if emissive_colour is not None:
        emissive = material_editing.create_material_expression(
            material, unreal.MaterialExpressionConstant3Vector, -320, 150)
        emissive.set_editor_property("constant", unreal.LinearColor(*emissive_colour, 1.0))
        material_editing.connect_material_property(emissive, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    material_editing.recompile_material(material)
    library.save_loaded_asset(material, only_if_is_dirty=False)
    return material


housing_material = simple_material(
    "M_CA_MW_PR008_LuminaireHousing_v078", (0.025, 0.031, 0.033), 0.48)
diffuser_material = simple_material(
    "M_CA_MW_PR008_LuminaireDiffuser_v078", (0.62, 0.67, 0.69), 0.30,
    (5.4, 5.9, 6.2))


def cube(label, centre, dimensions, material, tags):
    actor = actors.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(*centre), unreal.Rotator())
    if actor is None:
        raise RuntimeError(f"Could not spawn {label}")
    actor.set_actor_label(PREFIX + label)
    actor.tags = [unreal.Name(value) for value in (
        "LB.Asset.Candidate.v078", "LB.Asset.CandidateNotPromoted", *tags)]
    component = actor.static_mesh_component
    component.set_static_mesh(library.load_asset("/Engine/BasicShapes/Cube.Cube"))
    component.set_world_scale3d(unreal.Vector(
        dimensions[0] / 100.0, dimensions[1] / 100.0, dimensions[2] / 100.0))
    component.set_material(0, material)
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_collision_profile_name(unreal.Name("NoCollision"))
    component.set_editor_property("can_ever_affect_navigation", False)
    return actor


fixture_specs = [
    ("West", (-830.0, -1995.0, 1040.0)),
    ("Centre", (-500.0, -1995.0, 1040.0)),
    ("East", (-170.0, -1995.0, 1040.0)),
]
fixtures = []
lights = []
for label, location in fixture_specs:
    housing = cube(
        f"Luminaire_{label}_Housing", location, (190.0, 38.0, 9.0), housing_material,
        ("LB.Lighting.PR008.Fixture", "LB.Navigation.Neutral"))
    diffuser = cube(
        f"Luminaire_{label}_Diffuser", (location[0], location[1], location[2] - 5.5),
        (174.0, 28.0, 2.0), diffuser_material,
        ("LB.Lighting.PR008.Emissive", "LB.Navigation.Neutral"))
    light = actors.spawn_actor_from_class(
        unreal.RectLight, unreal.Vector(location[0], location[1], location[2] - 12.0), unreal.Rotator())
    if light is None:
        raise RuntimeError(f"Could not spawn {label} rect light")
    light.set_actor_label(PREFIX + f"LIGHT_Overhead_{label}")
    light.tags = [unreal.Name(value) for value in (
        "LB.Asset.Candidate.v078", "LB.Asset.CandidateNotPromoted", "LB.Lighting.PR008.Industrial")]
    light.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
        light.get_actor_location(), unreal.Vector(location[0], location[1], 80.0)), False)
    light.rect_light_component.set_editor_properties({
        "intensity": 22000.0,
        "attenuation_radius": 1450.0,
        "source_width": 174.0,
        "source_height": 28.0,
        "light_color": unreal.Color(224, 238, 246, 255),
        "cast_shadows": True,
        "affect_global_illumination": True,
        "affect_reflection": True,
    })
    fixtures.extend((housing, diffuser))
    lights.append(light)


def broad_fill(label, location, target, intensity, colour):
    light = actors.spawn_actor_from_class(unreal.RectLight, unreal.Vector(*location), unreal.Rotator())
    if light is None:
        raise RuntimeError(f"Could not spawn fill {label}")
    light.set_actor_label(PREFIX + "LIGHT_" + label)
    light.tags = [unreal.Name(value) for value in (
        "LB.Asset.Candidate.v078", "LB.Asset.CandidateNotPromoted", "LB.Lighting.PR008.CameraFill")]
    light.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
        light.get_actor_location(), unreal.Vector(*target)), False)
    light.rect_light_component.set_editor_properties({
        "intensity": intensity,
        "attenuation_radius": 1050.0,
        "source_width": 250.0,
        "source_height": 160.0,
        "light_color": unreal.Color(*colour, 255),
        "cast_shadows": False,
        "affect_global_illumination": False,
        "affect_reflection": True,
    })
    return light


lights.extend([
    broad_fill("OperatorFill", (-520.0, -2740.0, 430.0), (-500.0, -1995.0, 125.0),
               6200.0, (218, 232, 241)),
    broad_fill("DischargeFill", (240.0, -1430.0, 360.0), (-85.0, -1995.0, 90.0),
               5200.0, (242, 226, 207)),
])

capture = actors.spawn_actor_from_class(
    unreal.SphereReflectionCapture, unreal.Vector(-485.0, -1995.0, 190.0), unreal.Rotator())
if capture is None:
    raise RuntimeError("Could not spawn local PR-008 reflection capture")
capture.set_actor_label(PREFIX + "Reflection_LocalMachine")
capture.tags = [unreal.Name(value) for value in (
    "LB.Asset.Candidate.v078", "LB.Asset.CandidateNotPromoted", "LB.Reflection.PR008.Local")]
capture.capture_component.set_editor_properties({
    "influence_radius": 900.0,
    "brightness": 0.92,
    "runtime_capture": True,
    "reflection_source_type": unreal.ReflectionSourceType.CAPTURED_SCENE,
    "runtime_skylight_scale": unreal.LinearColor(0.12, 0.15, 0.17, 1.0),
})

column = next((actor for actor in actors.get_all_level_actors()
               if actor.get_actor_label() == "LB_PRESS_Column_0_-2250"), None)
if column is None or column.get_editor_property("hidden"):
    raise RuntimeError("The genuine hall column must remain present in v078")

if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")
library.save_directory(DEST, only_if_is_dirty=False, recursive=True)

payload = {
    "$schema": "line-boss/audit/press-shop-pr008-reflection-environment-candidate-v078/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "LOCAL_INDUSTRIAL_LIGHTING_REFLECTION_ENVIRONMENT_BUILT_FROM_RETAINED_V077__ALL_GATES_AND_FRESH_VISUAL_REVIEW_REQUIRED__NOT_PROMOTED",
    "map": MAP,
    "base_map": BASE,
    "strategy": "physical overhead luminaires, restrained camera fills and one local runtime reflection capture; v077 smooth materials unchanged",
    "fixture_count": len(fixtures) // 2,
    "fixture_mesh_count": len(fixtures),
    "light_count": len(lights),
    "reflection_capture": capture.get_actor_label(),
    "new_dressing_collision": "NoCollision",
    "new_dressing_navigation": "neutral",
    "fixed_hall_column_preserved": column.get_actor_label(),
    "control_room_viewing_priority": "fixed CCTV readability with drone-close inspection retained",
    "accepted_pr004_v006_preserved": True,
    "rejected_pr004_v007_v010_unchanged": True,
    "rejected_pr008_v076_unchanged": True,
    "retained_v077_unchanged": True,
    "promotion_authorized": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(
    f"LINE_BOSS_PR008_V078_ENVIRONMENT_BUILD_PASS fixtures={len(fixtures) // 2} "
    f"lights={len(lights)} reflection=1")
unreal.SystemLibrary.quit_editor()
