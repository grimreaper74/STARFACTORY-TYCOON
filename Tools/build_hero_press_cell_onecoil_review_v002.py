"""Create an isolated native-Unreal review level for the cleaned v002 press.

No existing factory level is loaded, edited, or saved.
"""
import json
import math
from pathlib import Path

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/HeroPressCell_MeshyOneCoil_v002/Maps/LB_HeroPressCell_MeshyOneCoil_Review_v002"
MESH_PATH = "/Game/LineBoss/Candidates/PressShop/HeroPressCell_MeshyOneCoil_v002/SM_LB_PS_HeroPressCell_MeshyOneCoil_v002"
BODY_MATERIAL_PATH = "/Game/LineBoss/Candidates/PressShop/HeroPressCell_MeshyOneCoil_v002/Materials/MI_LB_PS_HeroPressCell_MeshyOneCoil_v002"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "hero_press_cell_onecoil_review_map_v002.json"
TAG = unreal.Name("LB.HeroPressCell.OneCoil.V002.Review")


def fail(message):
    raise RuntimeError("HERO_PRESS_V002_REVIEW_MAP_FAIL: " + message)


def aim(source, target):
    dx, dy, dz = target.x - source.x, target.y - source.y, target.z - source.z
    horizontal = math.sqrt(dx * dx + dy * dy)
    return unreal.Rotator(math.degrees(math.atan2(dz, horizontal)), math.degrees(math.atan2(dy, dx)), 0.0)


def spawn(class_type, location, label, rotation=None):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(class_type, unreal.Vector(*location), rotation or unreal.Rotator())
    if actor is None:
        fail("could not spawn {}".format(class_type))
    actor.tags = [TAG, unreal.Name("LB.Environment.VisualOnly"), unreal.Name("LB.NotProcessWIP")]
    actor.set_actor_label(label)
    return actor


mesh = unreal.load_asset(MESH_PATH)
body_material = unreal.load_asset(BODY_MATERIAL_PATH)
plane = unreal.load_asset("/Engine/BasicShapes/Plane")
if not isinstance(mesh, unreal.StaticMesh) or body_material is None or not isinstance(plane, unreal.StaticMesh):
    fail("required candidate assets are missing")
if unreal.EditorAssetLibrary.does_asset_exist(MAP):
    fail("review level already exists; do not overwrite it")
if not unreal.EditorLevelLibrary.new_level(MAP):
    fail("could not create isolated review level")
world = unreal.EditorLevelLibrary.get_editor_world()
if world is None or world.get_name() != MAP.rsplit("/", 1)[-1]:
    fail("new candidate level did not become the active editor world")

floor = spawn(unreal.StaticMeshActor, (0.0, 0.0, -2.0), "HeroPressCellV002_ReviewFloor")
floor.static_mesh_component.set_static_mesh(plane)
floor.static_mesh_component.set_world_scale3d(unreal.Vector(60.0, 60.0, 1.0))

press = spawn(unreal.StaticMeshActor, (0.0, 0.0, 0.0), "HeroPressCell_OneCoil_CleanedV002")
press_component = press.static_mesh_component
press_component.set_static_mesh(mesh)
press_component.set_material(0, body_material)

sun = spawn(unreal.DirectionalLight, (0.0, 0.0, 2500.0), "HeroPressCellV002_KeySun")
sun.light_component.set_editor_property("intensity", 2.0)
sun.light_component.set_editor_property("use_temperature", True)
sun.light_component.set_editor_property("temperature", 5200.0)
sun.set_actor_rotation(unreal.Rotator(-35.0, -35.0, 0.0), False)

sky = spawn(unreal.SkyLight, (0.0, 0.0, 1400.0), "HeroPressCellV002_Sky")
sky.light_component.set_editor_property("intensity", 0.75)
sky.light_component.set_editor_property("real_time_capture", True)

for location, energy, colour, label in (
    ((800.0, -1200.0, 1400.0), 55000.0, unreal.LinearColor(1.0, 0.78, 0.58, 1.0), "HeroPressCellV002_WarmKey"),
    ((-1100.0, 950.0, 1050.0), 28000.0, unreal.LinearColor(0.75, 0.85, 1.0, 1.0), "HeroPressCellV002_CoolFill"),
):
    light = spawn(unreal.RectLight, location, label)
    light.light_component.set_editor_property("intensity", energy)
    light.light_component.set_editor_property("intensity_units", unreal.LightUnits.LUMENS)
    light.light_component.set_editor_property("source_width", 900.0)
    light.light_component.set_editor_property("source_height", 600.0)
    light.light_component.set_editor_property("light_color", colour)
    light.set_actor_rotation(aim(light.get_actor_location(), unreal.Vector(0.0, 0.0, 350.0)), False)

camera = spawn(unreal.CameraActor, (2300.0, -2600.0, 1500.0), "HeroPressCellV002_ReviewCamera")
camera.set_actor_rotation(aim(camera.get_actor_location(), unreal.Vector(0.0, 0.0, 350.0)), False)
camera.get_camera_component().set_editor_property("field_of_view", 52.0)
unreal.EditorLevelLibrary.set_level_viewport_camera_info(camera.get_actor_location(), camera.get_actor_rotation())

unreal.EditorLevelLibrary.save_current_level()
report = {
    "status": "PASS__ISOLATED_V002_REVIEW_MAP_CREATED",
    "map": MAP,
    "press": {"asset": MESH_PATH, "body_material": BODY_MATERIAL_PATH, "location_cm": [0.0, 0.0, 0.0]},
    "camera": {"location_cm": [2300.0, -2600.0, 1500.0], "target_cm": [0.0, 0.0, 350.0]},
    "lighting": {"directional": 1, "skylight": 1, "rect_lights": 2},
    "map_isolation": "new v002 candidate map; no existing map was loaded, changed, or saved",
}
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("LINE_BOSS_HERO_PRESS_V002_REVIEW_MAP=" + json.dumps(report, sort_keys=True))
