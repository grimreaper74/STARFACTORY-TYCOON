"""Fence weld's 18 robot cells with the project's authored guarding.

Press's apparent density is dominated by safety guarding - 130 SM_LB_GuardPost_1500 and
119 SM_LB_GuardPanel_2000 - so this is the largest density gain available with no
authoring at all, and it follows press's own recipe rather than inventing one.

Cells are fenced on the two sides PARALLEL to travel and left open at the line ends,
which is how a real robot cell is guarded: the conveyor runs through, people do not.
Each cell gets an interlock box on the access side.

Station positions from CanonicalLocation in LBOneFactoryBodyWeldStarterLayout.cpp -
2000 cm pitch, run A at Y -7000 from X -3050 westward, run B at Y -11200 from X -19050
eastward.

Idempotent. Run with -ExecutePythonScript.
"""
import io
import json
import os

import unreal

TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
TAG = "LB.Weld.Guarding"
PANEL = "/Game/LineBoss/IndustrialKit/Safety/Barrier/SM_LB_GuardPanel_2000_v001"
POST = "/Game/LineBoss/IndustrialKit/Safety/Barrier/SM_LB_GuardPost_1500_v001"
INTERLOCK = "/Game/LineBoss/IndustrialKit/Safety/Barrier/SM_LB_GuardInterlockBox_v001"
OUT = os.environ.get("LB_GUARD_OUT", "C:/Temp/lb_guard.json")

# MEASURED, and the naming is in MILLIMETRES: SM_LB_GuardPanel_2000 is 200 cm long
# (200.0 x 7.6 x 128.5) and SM_LB_GuardPost_1500 is 153.7 cm tall. Reading 2000 as
# centimetres spaced the panels 18 m apart and the fence read as scattered frames.
PANEL_LEN = 200.0
FENCE_HALF_Y = 1900.0   # just outside the station's 3200 cm depth
FENCE_RUN_X = 1800.0    # fenced length along travel, inside the 2000 cm pitch

STATIONS = [(-3050.0 - n * 2000.0, -7000.0) for n in range(9)]
STATIONS += [(-19050.0 + n * 2000.0, -11200.0) for n in range(9)]

LEVEL_SUB = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTOR_SUB = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
REPORT = {"panels": 0, "posts": 0, "interlocks": 0, "cleared": 0}

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


def place(path, x, y, yaw, kind):
    a = asset(path)
    lift = -a.get_bounding_box().min.z
    actor = ACTOR_SUB.spawn_actor_from_object(
        a, unreal.Vector(x, y, lift), unreal.Rotator(0.0, yaw, 0.0))
    if actor is None:
        return
    actor.tags = [unreal.Name(TAG), unreal.Name("LB.Environment.VisualOnly"),
                  unreal.Name("LB.NotProcessWIP")]
    actor.set_actor_label("Weld_{}".format(kind))
    REPORT[kind] += 1


for index, (sx, sy) in enumerate(STATIONS):
    panels_per_side = int(FENCE_RUN_X // PANEL_LEN)
    start_x = sx - FENCE_RUN_X * 0.5
    for side in (-1.0, 1.0):
        fence_y = sy + side * FENCE_HALF_Y
        for n in range(panels_per_side):
            place(PANEL, start_x + PANEL_LEN * (n + 0.5), fence_y, 0.0, "panels")
        # A post at every panel joint, including both ends.
        for n in range(panels_per_side + 1):
            place(POST, start_x + PANEL_LEN * n, fence_y, 0.0, "posts")
    # One interlocked access point per cell, on the north fence line.
    place(INTERLOCK, sx, sy + FENCE_HALF_Y, 0.0, "interlocks")

LEVEL_SUB.save_current_level()
REPORT["total"] = REPORT["panels"] + REPORT["posts"] + REPORT["interlocks"]
with io.open(OUT, "w", encoding="utf-8") as h:
    h.write(json.dumps(REPORT, indent=1))
unreal.log("LINE_BOSS_WELD_GUARDING {} -> {}".format(json.dumps(REPORT), OUT))
