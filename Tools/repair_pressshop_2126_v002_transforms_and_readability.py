"""Repair explicit rotations and working-height lighting in Press Shop v002.

UE 5.8 commandlet spawning accepted the initial actor placements but did not
retain the passed rotations.  This map-local repair explicitly sets every
authored visual transform.  It also places the six B_stylized fixtures at the
actual open-bay height (8.5m), and adds only functional task lights permitted
by the visual standard for material readability.
"""

import hashlib
import json
import math
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v002/Maps/LB_PressShop_2126_Steam_v002"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_v002_transform_readability_repair.json"
TAG = unreal.Name("LB.PressShop.2126.v002.TransformRepair")


def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def aim(source, target):
    dx, dy, dz = target.x - source.x, target.y - source.y, target.z - source.z
    flat = math.sqrt(dx * dx + dy * dy)
    return unreal.Rotator(math.degrees(math.atan2(dz, flat)), math.degrees(math.atan2(dy, dx)), 0.0)


def require(actors, label):
    actor = actors.get(label)
    if actor is None:
        raise RuntimeError("Missing v002 actor: " + label)
    return actor


if not PROTECTED.is_file():
    raise RuntimeError("Protected v438 map is missing")
before = digest(PROTECTED)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load v002 candidate map")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
if any(TAG in actor.tags for actor in actors.values()):
    raise RuntimeError("Transform repair already applied; refusing to alter it again")

changed = []
for label, yaw in (
    ("S00 | wrapped master coil | project reuse", 90.0),
    ("S00 | bare master coil | project reuse", 90.0),
    ("MESHY v002 | S02 Draw / form", 0.0),
    ("MESHY v002 | S03 Trim", 90.0),
    ("MESHY v002 | S04 Pierce", 0.0),
    ("MESHY v002 | S05 Flange / hem", 90.0),
    ("MESHY v002 | S06 Vision / outfeed", 90.0),
    ("ROBOT v002 | S01 laser-tend robot", -155.0),
    ("ROBOT v002 | S02 draw quality robot", 180.0),
    ("ROBOT v002 | S04 pierce handling robot", 180.0),
    ("ROBOT v002 | S06 vision stack robot", -20.0),
):
    actor = require(actors, label)
    actor.set_actor_rotation(unreal.Rotator(0.0, yaw, 0.0), False)
    for component in actor.get_components_by_class(unreal.PrimitiveComponent):
        component.set_visibility(True, True)
        component.set_render_in_main_pass(True)
    changed.append(label)

# The original values were centimetres but the first script treated the lights
# as 82m high.  850cm is an 8.5m open-bay hang height, which is why B_stylized
# reads in its test hall without changing its documented six/1200lm contract.
for index, x in enumerate((-12500.0, -8500.0, -4500.0, -500.0, 3500.0, 7200.0), start=1):
    actor = require(actors, "B_stylized | 1200 lm fixture %02d" % index)
    actor.set_actor_location(unreal.Vector(x, -600.0, 850.0), False, False)
    actor.set_actor_rotation(unreal.Rotator(-90.0, 0.0, 0.0), False)
    actor.tags = list(actor.tags) + [TAG]
    changed.append(actor.get_actor_label())

# Same sparse, roofless masts, corrected from 78m to a believable 14m. They
# remain at the perimeter so screenshots don't become a forest of columns.
for label, actor in actors.items():
    if not label.startswith("2126 v002 | open-air mast "):
        continue
    location = actor.get_actor_location()
    actor.set_actor_location(unreal.Vector(location.x, location.y, 700.0), False, False)
    actor.set_actor_scale3d(unreal.Vector(2.6, 2.6, 14.0))
    actor.tags = list(actor.tags) + [TAG]
    changed.append(label)

# The visual standard explicitly permits process/task lights. These four warm
# work lights illuminate only the active die/robot interfaces; they are not a
# replacement for the six fixture B_stylized calibration above.
for index, (label, source, target) in enumerate((
    ("S00 coil change task light", (-13700.0, -1500.0, 700.0), (-13200.0, 0.0, 260.0)),
    ("S02 die quality task light", (-4800.0, -1500.0, 700.0), (-4200.0, 0.0, 300.0)),
    ("S04 pierce robot task light", (-800.0, -1500.0, 700.0), (-200.0, 0.0, 300.0)),
    ("S06 vision robot task light", (4000.0, -1600.0, 700.0), (3500.0, 0.0, 300.0)),
), start=1):
    light = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.RectLight, unreal.Vector(*source), aim(unreal.Vector(*source), unreal.Vector(*target)))
    if light is None:
        raise RuntimeError("Could not add functional task light")
    light.set_actor_label("2126 v002 | " + label)
    light.tags = [TAG, unreal.Name("LB.Lighting.FunctionalTask"), unreal.Name("LB.Visual.2126")]
    component = light.light_component
    component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
    component.set_editor_property("intensity", 16000.0)
    component.set_editor_property("intensity_units", unreal.LightUnits.LUMENS)
    component.set_editor_property("source_width", 460.0)
    component.set_editor_property("source_height", 220.0)
    component.set_editor_property("use_temperature", True)
    component.set_editor_property("temperature", 5000.0)
    changed.append(light.get_actor_label())

camera_intents = (
    ("CAM v002 | steam hero press run", (-8500.0, -5300.0, 610.0), (-550.0, 0.0, 370.0)),
    ("CAM v002 | coil-to-press story", (-17800.0, -3300.0, 450.0), (-12000.0, 0.0, 360.0)),
    ("CAM v002 | draw plus robot", (-7800.0, -3600.0, 480.0), (-4200.0, -150.0, 330.0)),
    ("CAM v002 | press automation", (-2800.0, -4100.0, 500.0), (-200.0, -250.0, 320.0)),
)
for label, source, target in camera_intents:
    camera = require(actors, label)
    camera.set_actor_location(unreal.Vector(*source), False, False)
    camera.set_actor_rotation(aim(unreal.Vector(*source), unreal.Vector(*target)), False)
    camera.tags = list(camera.tags) + [TAG]
    changed.append(label)

hero = require(actors, "CAM v002 | steam hero press run")
unreal.EditorLevelLibrary.set_level_viewport_camera_info(hero.get_actor_location(), hero.get_actor_rotation())
if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save v002 repaired candidate")
after = digest(PROTECTED)
if before != after:
    raise RuntimeError("Protected v438 map changed during v002 repair")

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__EXPLICIT_TRANSFORMS_AND_WORKING_HEIGHT_LIGHTING_REPAIRED",
    "candidate_map": MAP,
    "changed": changed,
    "b_stylized_unchanged_contract": {"fixture_count": 6, "lumens_each": 1200, "sun": 0.30, "sky": 0.20, "exposure_bias": -0.50},
    "functional_task_lights": 4,
    "roof_created": False,
    "protected_v438_sha256_before": before,
    "protected_v438_sha256_after": after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_V002_TRANSFORM_READABILITY_REPAIR_PASS")
