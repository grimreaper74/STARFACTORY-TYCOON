"""Fence a shop's station cells with the project's authored guarding.

Generalised from the verified weld pass. Press's density is dominated by this guarding
(130 posts, 119 panels), so it is the largest gain available with no authoring.

MEASURED, and the naming is MILLIMETRES: SM_LB_GuardPanel_2000 is 200.0 x 7.6 x 128.5 cm
and SM_LB_GuardPost_1500 is 153.7 cm tall. Reading the suffix as centimetres spaced
panels 18 m apart and the fence read as scattered frames.

Cells are fenced on the two sides parallel to travel and open at the line ends - the
conveyor runs through, people do not - with one interlocked access point per cell.

NOT for paint. Paint's 8 stations are dip tanks, spray booths and ovens: enclosed
process structures, not fenced robot cells. Fencing them would misrepresent the process.
Booth enclosures are an authoring item.

  LB_SHOP=Assembly UnrealEditor-Cmd.exe <uproject> -ExecutePythonScript=Tools/build_shop_cell_guarding.py
"""
import io
import json
import os

import unreal

TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
PANEL = "/Game/LineBoss/IndustrialKit/Safety/Barrier/SM_LB_GuardPanel_2000_v001"
POST = "/Game/LineBoss/IndustrialKit/Safety/Barrier/SM_LB_GuardPost_1500_v001"
INTERLOCK = "/Game/LineBoss/IndustrialKit/Safety/Barrier/SM_LB_GuardInterlockBox_v001"
PANEL_LEN = 200.0
OUT = os.environ.get("LB_GUARD_OUT", "C:/Temp/lb_guard.json")

# Station positions from each shop's CanonicalLocation, plus a fence offset across
# travel and a fenced run along it that stays inside the station pitch.
def weld_stations():
    s = [(-3050.0 - n * 2000.0, -7000.0) for n in range(9)]
    s += [(-19050.0 + n * 2000.0, -11200.0) for n in range(9)]
    return s, 1900.0, 1800.0


def assembly_stations():
    s = [(4000.0 + n * 2200.0, 5500.0) for n in range(12)]
    s += [(28200.0 - n * 2200.0, 11500.0) for n in range(12)]
    return s, 1900.0, 2000.0


SHOPS = {"Body": weld_stations, "Assembly": assembly_stations}
SHOP = os.environ.get("LB_SHOP", "Assembly")
if SHOP not in SHOPS:
    raise RuntimeError("LB_SHOP must be one of {} (paint is excluded by design)".format(
        sorted(SHOPS)))
TAG = "LB.{}.Guarding".format(SHOP)
STATIONS, FENCE_HALF_Y, FENCE_RUN_X = SHOPS[SHOP]()

LEVEL_SUB = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTOR_SUB = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
REPORT = {"shop": SHOP, "panels": 0, "posts": 0, "interlocks": 0, "cleared": 0}

if not LEVEL_SUB.load_level(TARGET):
    raise RuntimeError("could not load target")
w = unreal.EditorLevelLibrary.get_editor_world()
if w is None or TARGET.rsplit("/", 1)[-1] != w.get_name():
    raise RuntimeError("wrong world; use -ExecutePythonScript")

for a in ACTOR_SUB.get_all_level_actors():
    if a and unreal.Name(TAG) in a.tags:
        ACTOR_SUB.destroy_actor(a)
        REPORT["cleared"] += 1

CACHE = {}


def asset(path):
    if path not in CACHE:
        got = unreal.load_asset(path)
        if got is None:
            raise RuntimeError("missing {}".format(path))
        CACHE[path] = got
    return CACHE[path]


def place(path, x, y, kind):
    a = asset(path)
    lift = -a.get_bounding_box().min.z
    actor = ACTOR_SUB.spawn_actor_from_object(
        a, unreal.Vector(x, y, lift), unreal.Rotator(0.0, 0.0, 0.0))
    if actor is None:
        return
    actor.tags = [unreal.Name(TAG), unreal.Name("LB.Environment.VisualOnly"),
                  unreal.Name("LB.NotProcessWIP")]
    actor.set_actor_label("{}_{}".format(SHOP, kind))
    REPORT[kind] += 1


per_side = int(FENCE_RUN_X // PANEL_LEN)
for sx, sy in STATIONS:
    start_x = sx - FENCE_RUN_X * 0.5
    for side in (-1.0, 1.0):
        fence_y = sy + side * FENCE_HALF_Y
        for n in range(per_side):
            place(PANEL, start_x + PANEL_LEN * (n + 0.5), fence_y, "panels")
        for n in range(per_side + 1):
            place(POST, start_x + PANEL_LEN * n, fence_y, "posts")
    place(INTERLOCK, sx, sy + FENCE_HALF_Y, "interlocks")

LEVEL_SUB.save_current_level()
REPORT["total"] = REPORT["panels"] + REPORT["posts"] + REPORT["interlocks"]
with io.open(OUT, "w", encoding="utf-8") as h:
    h.write(json.dumps(REPORT, indent=1))
unreal.log("LINE_BOSS_SHOP_GUARDING {}".format(json.dumps(REPORT)))
