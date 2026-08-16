"""Build isolated v191 whole-hall readability candidate from retained v190.

The candidate preserves the validated hook, coils, Sheet 2 layout and runtime
authority. It replaces black architectural envelope materials with restrained
factory liner finishes, adds one missing row of linear LED high-bays over the
support/logistics side, and uses broad low-energy north-wall wash without
decorating or obstructing the operational crane/maintenance corridor.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PR003PR004HookLightingMergeCandidate_v190"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR003PR004WholeHallReadabilityCandidate_v191"
DEST = "/Game/LineBoss/Candidates/PressShop/PR003PR004WholeHallReadability_v191"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_pr003_pr004_whole_hall_readability_build_v191.json"
BASE_PACKAGE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PR003PR004HookLightingMergeCandidate_v190.umap"

library = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
materials_api = unreal.MaterialEditingLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def constant_material(name, colour, roughness, metallic=0.0):
    material = tools.create_asset(name, DEST + "/Materials", unreal.Material, unreal.MaterialFactoryNew())
    if material is None:
        raise RuntimeError(f"could not create {name}")
    colour_node = materials_api.create_material_expression(
        material, unreal.MaterialExpressionConstant3Vector, -260, -40)
    colour_node.set_editor_property("constant", unreal.LinearColor(*colour, 1.0))
    rough = materials_api.create_material_expression(material, unreal.MaterialExpressionConstant, -260, 80)
    rough.set_editor_property("r", roughness)
    metal = materials_api.create_material_expression(material, unreal.MaterialExpressionConstant, -260, 150)
    metal.set_editor_property("r", metallic)
    materials_api.connect_material_property(colour_node, "", unreal.MaterialProperty.MP_BASE_COLOR)
    materials_api.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    materials_api.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    materials_api.recompile_material(material)
    library.save_loaded_asset(material, only_if_is_dirty=False)
    return material


def merge_tags(actor, additions):
    actor.tags = [unreal.Name(value) for value in dict.fromkeys(
        [str(value) for value in actor.tags] + additions)]


base_hash_before = sha256(BASE_PACKAGE)
if library.does_asset_exist(MAP):
    raise RuntimeError(f"refusing to overwrite preserved candidate {MAP}")
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"could not create isolated v191 from {BASE}")

materials = {
    "shell": constant_material("M_CA_MW_HallShellBacking_v191", (0.095, 0.108, 0.118), 0.90),
    "lower": constant_material("M_CA_MW_HallLowerConcreteLiner_v191", (0.155, 0.165, 0.172), 0.92),
    "upper": constant_material("M_CA_MW_HallUpperServiceLiner_v191", (0.115, 0.132, 0.145), 0.84),
    "roof": constant_material("M_CA_MW_HallRoofLiner_v191", (0.072, 0.082, 0.090), 0.86, 0.08),
}
common_tags = [
    "LB.Asset.Candidate.v191", "LB.Asset.CandidateNotPromoted",
    "LB.Environment.WholeHallReadability.v191", "LB.VisualCorrection.ArchitecturalEnvelope",
]

changed_surfaces = []
role_counts = {key: 0 for key in materials}
for actor in actors_api.get_all_level_actors():
    if not isinstance(actor, unreal.StaticMeshActor):
        continue
    label = actor.get_actor_label()
    role = None
    if label in ("LB_PRESS_Wall_North", "LB_PRESS_Wall_South", "LB_PRESS_Wall_West", "LB_PRESS_Wall_East"):
        role = "shell"
    elif label == "LB_INT_FRONT_NorthWallLowerLiner":
        role = "lower"
    elif label in ("LB_INT_FRONT_NorthWallUpperLiner", "LB_INT_FRONT_WestWallLiner"):
        role = "upper"
    elif label.startswith("LB_PR004_V028_SouthWallLiner_"):
        role = "upper"
    elif label.startswith("LB_PR004_V028_RoofLiner_"):
        role = "roof"
    if role is None:
        continue
    component = actor.static_mesh_component
    before = []
    for index in range(max(1, component.get_num_materials())):
        old = component.get_material(index)
        before.append(old.get_path_name() if old else None)
        component.set_material(index, materials[role])
    merge_tags(actor, common_tags + [f"LB.Environment.HallFinish.{role}"])
    role_counts[role] += 1
    changed_surfaces.append({
        "actor": label, "role": role, "before": before,
        "after": materials[role].get_path_name(),
    })

lens = library.load_asset(
    "/Game/LineBoss/Candidates/PressShop/IntegratedEnvironment_v107/Materials/M_CA_MW_LuminaireLens_v105")
cube = library.load_asset("/Engine/BasicShapes/Cube.Cube")
if lens is None or cube is None:
    raise RuntimeError("missing inherited luminaire assets")

high_bay_fixtures = []
high_bay_lights = []
for index, x in enumerate(range(-11800, 3001, 1600), start=1):
    fixture = actors_api.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(float(x), 2800.0, 1760.0), unreal.Rotator())
    fixture.set_actor_label(f"LB_ENV_V191_SupportLinearLED_{index:02d}")
    fixture.static_mesh_component.set_static_mesh(cube)
    fixture.set_actor_scale3d(unreal.Vector(7.0, 0.42, 0.10))
    fixture.static_mesh_component.set_material(0, lens)
    fixture.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    merge_tags(fixture, common_tags + ["LB.Environment.Luminaire.LinearLEDHighBay"])
    high_bay_fixtures.append(fixture.get_actor_label())

    light = actors_api.spawn_actor_from_class(
        unreal.RectLight, unreal.Vector(float(x), 2800.0, 1725.0), unreal.Rotator(-90.0, 0.0, 0.0))
    light.set_actor_label(f"LB_ENV_V191_SupportLinearLEDRect_{index:02d}")
    component = light.get_component_by_class(unreal.RectLightComponent)
    component.set_editor_properties({
        "intensity": 9.5,
        "source_width": 1250.0,
        "source_height": 110.0,
        "attenuation_radius": 2050.0,
        "cast_shadows": False,
        "light_color": unreal.Color(214, 225, 228, 255),
    })
    merge_tags(light, common_tags + ["LB.Environment.Light.LinearLEDHighBay"])
    high_bay_lights.append(light.get_actor_label())

wall_wash = []
for index, x in enumerate((-10000.0, -8000.0, -6000.0, -4000.0), start=1):
    location = unreal.Vector(x, -5000.0, 1050.0)
    target = unreal.Vector(x, -5930.0, 1080.0)
    light = actors_api.spawn_actor_from_class(
        unreal.RectLight, location, unreal.MathLibrary.find_look_at_rotation(location, target))
    light.set_actor_label(f"LB_ENV_V191_NorthWallBroadWash_{index:02d}")
    component = light.get_component_by_class(unreal.RectLightComponent)
    component.set_editor_properties({
        "intensity": 8.0,
        "source_width": 1750.0,
        "source_height": 1050.0,
        "attenuation_radius": 1450.0,
        "cast_shadows": False,
        "light_color": unreal.Color(211, 222, 226, 255),
    })
    merge_tags(light, common_tags + ["LB.Environment.Light.BroadWallWash"])
    wall_wash.append(light.get_actor_label())


def add_camera(label, location, target, fov):
    camera = actors_api.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    camera.set_actor_label(label)
    camera.set_actor_rotation(
        unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(), unreal.Vector(*target)), False)
    camera.camera_component.set_editor_properties({
        "field_of_view": fov, "aspect_ratio": 16.0 / 9.0, "constrain_aspect_ratio": True,
    })
    merge_tags(camera, common_tags + ["LB.Camera.Validation", "LB.Camera.Fixed.WholeHallReadability.v191"])
    return camera


cameras = [
    add_camera("LB_ENV_V191_CAM_FrontEndFlow", (-10600.0, 900.0, 980.0), (-7200.0, -2100.0, 520.0), 59.0),
    add_camera("LB_ENV_V191_CAM_PR003PR004Management", (-10300.0, 1450.0, 720.0), (-5900.0, -2850.0, 470.0), 62.0),
    add_camera("LB_ENV_V191_CAM_NorthWallCell", (-9600.0, 250.0, 660.0), (-6500.0, -5100.0, 850.0), 57.0),
    add_camera("LB_ENV_V191_CAM_LogisticsSupport", (-9000.0, 1200.0, 420.0), (-2200.0, 2800.0, 320.0), 62.0),
]

failures = []
expected_roles = {"shell": 4, "lower": 1, "upper": 7, "roof": 20}
if role_counts != expected_roles:
    failures.append(f"surface role counts {role_counts} != {expected_roles}")
if len(changed_surfaces) != 32:
    failures.append(f"expected 32 surface bindings, found {len(changed_surfaces)}")
if len(high_bay_fixtures) != 10 or len(high_bay_lights) != 10:
    failures.append("expected ten support-side linear LED high-bays")
if len(wall_wash) != 4 or len(cameras) != 4:
    failures.append("unexpected broad-wall-wash or fixed-camera count")
if not levels.save_current_level():
    failures.append("could not save isolated v191")
library.save_directory(DEST, only_if_is_dirty=False, recursive=True)
base_hash_after = sha256(BASE_PACKAGE)
if base_hash_after != base_hash_before:
    failures.append("protected retained v190 package changed")

report = {
    "$schema": "cairnwell/audit/press-shop-pr003-pr004-whole-hall-readability-build-v191/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__MUTED_ARCHITECTURAL_ENVELOPE_AND_LINEAR_LED_HIGH_BAY_READABILITY_BUILT__LIVE_VISUAL_GATE_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__V191_BUILD__NOT_PROMOTED",
    "source_map": BASE, "map": MAP,
    "changed_surface_count": len(changed_surfaces), "surface_role_counts": role_counts,
    "linear_led_high_bay_fixtures": high_bay_fixtures,
    "linear_led_high_bay_lights": high_bay_lights,
    "north_wall_broad_wash": wall_wash,
    "fixed_cameras": [camera.get_actor_label() for camera in cameras],
    "operational_corridor_geometry_changed": False,
    "coil_hook_agv_crane_navigation_collision_or_gameplay_authority_changed": False,
    "protected_v190_sha256_before": base_hash_before,
    "protected_v190_sha256_after": base_hash_after,
    "promotion_authorized": False,
    "press_shop_complete": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"status": report["status"], "roles": role_counts, "failures": failures}, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
