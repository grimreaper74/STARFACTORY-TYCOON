"""Tighten the real Meshy press train after measuring its imported bounds.

The first placement correction proved that the five reusable Meshy assets load
and preserve their materials, but used a blockout-scale pitch. This v002 map
only correction moves the already-placed meshes to their measured production
clearance and hides the superseded oversized extension dressing. Nothing is
deleted and no protected map or mesh asset is edited.
"""
import json
import math
from pathlib import Path

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
ROOT = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Materials"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_meshy_pitch_v002.json"
TAG = unreal.Name("LB.PressShop.2126.MeshyPitch.v002")
SUPERSEDED = unreal.Name("LB.PressShop.2126.MeshyPitch.v001.Hidden")

# Derived from actual mesh bounds, accounting for source-heading yaws. These
# centres retain 3 m or more between envelopes and clear the incoming bridge.
LINE = (
    ("MESHY | S02 Draw / form | reused press asset", -4200.0),
    ("MESHY | S03 Trim | reused press asset", -2100.0),
    ("MESHY | S04 Pierce | reused press asset", -200.0),
    ("MESHY | S05 Flange / hem | reused press asset", 1600.0),
    ("MESHY | S06 Vision / outfeed | reused press asset", 3500.0),
)

HIDE_PREFIXES = (
    "2126 | Meshy line deck extension",
    "2126 | Meshy line operator avenue",
    "2126 | Meshy line service avenue",
    "2126 | Meshy process zone |",
    "2126 | station slab |",
    "2126 | Meshy line open-bay mast",
    "2126 | Meshy line mast safety base",
    "2126 | Meshy line gantry rail",
)


def fail(message):
    raise RuntimeError("PRESSSHOP_2126_MESHY_PITCH_V002_FAIL: " + message)


def aim(source, target):
    dx, dy, dz = target.x - source.x, target.y - source.y, target.z - source.z
    flat = math.sqrt(dx * dx + dy * dy)
    return unreal.Rotator(math.degrees(math.atan2(dz, flat)), math.degrees(math.atan2(dy, dx)), 0.0)


def hide(actor):
    actor.set_actor_hidden_in_game(True)
    actor.tags = list(actor.tags) + [SUPERSEDED]
    for component in actor.get_components_by_class(unreal.PrimitiveComponent):
        component.set_visibility(False, True)


def cube(label, location, dimensions, material, role):
    base = unreal.load_asset("/Engine/BasicShapes/Cube")
    if not isinstance(base, unreal.StaticMesh):
        fail("native cube unavailable")
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator())
    if actor is None:
        fail("could not create " + label)
    actor.set_actor_label(label)
    actor.tags = [TAG, unreal.Name(role)]
    component = actor.static_mesh_component
    component.set_static_mesh(base)
    component.set_world_scale3d(unreal.Vector(dimensions[0] / 100.0, dimensions[1] / 100.0, dimensions[2] / 100.0))
    component.set_material(0, material)
    return actor


if not unreal.EditorAssetLibrary.does_asset_exist(MAP):
    fail("fresh candidate map missing")
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    fail("could not load fresh candidate map")

actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
if any(TAG in actor.tags for actor in actors):
    fail("v002 pitch tag already exists; refusing duplicate correction")

by_label = {actor.get_actor_label(): actor for actor in actors}
missing = [label for label, _ in LINE if label not in by_label]
if missing:
    fail("real Meshy press actors are missing: " + ", ".join(missing))

for label, x in LINE:
    actor = by_label[label]
    old = actor.get_actor_location()
    actor.set_actor_location(unreal.Vector(x, old.y, old.z), False, False)
    actor.tags = list(actor.tags) + [TAG]

hidden = []
for actor in actors:
    if any(actor.get_actor_label().startswith(prefix) for prefix in HIDE_PREFIXES):
        hide(actor)
        hidden.append(actor.get_actor_label())

if len(hidden) < 10:
    fail("expected the v001 oversized dressing before superseding it")

floor = unreal.load_asset(ROOT + "/M_LB_PS2126_Floor")
pale_green = unreal.load_asset(ROOT + "/M_LB_PS2126_PaintedPaleGreen")
cream = unreal.load_asset(ROOT + "/M_LB_PS2126_CreamLane")
yellow = unreal.load_asset(ROOT + "/M_LB_PS2126_SafetyYellow")
if not all(isinstance(item, unreal.Material) for item in (floor, pale_green, cream, yellow)):
    fail("candidate materials missing")

# New pieces lie within the existing open deck: no roof, facade or shell.
for label, x in LINE:
    station = label.replace("MESHY | ", "").replace(" | reused press asset", "")
    cube("2126 | compact process zone | " + station, (x, 0.0, 8.0), (1800.0, 7200.0, 28.0), pale_green, "LB.PressShop.ProcessZone")
    cube("2126 | compact station plate | " + station, (x, -4050.0, 18.0), (1550.0, 360.0, 36.0), yellow, "LB.PressShop.StationID")

cube("2126 | compact operator avenue", (-5200.0, -5200.0, 18.0), (24200.0, 1350.0, 36.0), cream, "LB.PressShop.Access")
cube("2126 | compact service avenue", (-5200.0, 5200.0, 18.0), (24200.0, 1000.0, 36.0), cream, "LB.PressShop.Access")

for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    label = actor.get_actor_label()
    if label == "CAM | 2126 Steam hero overview":
        location = unreal.Vector(-14500.0, -19500.0, 6800.0)
        actor.set_actor_location(location, False, False)
        actor.set_actor_rotation(aim(location, unreal.Vector(-300.0, 0.0, 2300.0)), False)
        actor.get_cine_camera_component().set_editor_property("current_focal_length", 36.0)
    elif label == "CAM | 2126 operator line":
        location = unreal.Vector(-10200.0, -13500.0, 4400.0)
        actor.set_actor_location(location, False, False)
        actor.set_actor_rotation(aim(location, unreal.Vector(-600.0, 0.0, 2200.0)), False)
        actor.get_cine_camera_component().set_editor_property("current_focal_length", 42.0)
    elif label == "CAM | 2126 draw nexus":
        location = unreal.Vector(-10400.0, -8600.0, 3300.0)
        actor.set_actor_location(location, False, False)
        actor.set_actor_rotation(aim(location, unreal.Vector(-4200.0, 0.0, 2200.0)), False)
        actor.get_cine_camera_component().set_editor_property("current_focal_length", 48.0)

hero_location = unreal.Vector(-10200.0, -13500.0, 4400.0)
unreal.EditorLevelLibrary.set_level_viewport_camera_info(hero_location, aim(hero_location, unreal.Vector(-600.0, 0.0, 2200.0)))

if not unreal.EditorLevelLibrary.save_current_level():
    fail("could not save compact Meshy line correction")

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__MESHY_PRESS_LINE_COMPACTED_FROM_MEASURED_IMPORT_BOUNDS",
    "map": MAP,
    "candidate_only": True,
    "measured_envelope_pitch_cm": {label: x for label, x in LINE},
    "hidden_not_deleted_oversized_v001_dressing": hidden,
    "created_compact_zones": len(LINE),
    "no_roof_or_wall_mesh_created": True,
    "honest_status": "candidate presentation map only; still needs in-editor visual review",
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_MESHY_PITCH_V002_PASS: compacted=%d hidden=%d" % (len(LINE), len(hidden)))
