"""Stand a lit gantry arch over each of paint's 8 stations.

Positions are READ from the per-station contract table in
LBOneFactoryPaintStarterLayout.cpp:64-85, not computed. Paint is unlike weld and
assembly: it has no CanonicalLocation formula, and its pitches are irregular and
process-driven - 1700, 1700, 1400, 1800, 2200, 1700, 1300 - so any assumed grid would
have been wrong.

Same verified arch as weld and assembly: SM_LampArch01 at 1.6x, no rotation. The 1261
cm span at that scale covers the widest paint footprint (1200 cm) and the 941 cm height
clears the tallest (650 cm).

Idempotent. Run with -ExecutePythonScript.
"""
import io
import json
import os

import unreal

TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
TAG = "LB.Paint.Gantry"
ARCH = "/Game/Meshes/SM_LampArch01"
SCALE = 1.6
OUT = os.environ.get("LB_GANTRY_OUT", "C:/Temp/lb_gantry.json")

STATION_X = [0.0, 1700.0, 3400.0, 4800.0, 6600.0, 8800.0, 10500.0, 11800.0]
STATION_Y = -8500.0

LEVEL_SUB = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTOR_SUB = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
REPORT = {"placed": 0, "cleared": 0}

if not LEVEL_SUB.load_level(TARGET):
    raise RuntimeError("could not load target")
w = unreal.EditorLevelLibrary.get_editor_world()
if w is None or TARGET.rsplit("/", 1)[-1] != w.get_name():
    raise RuntimeError("wrong world; use -ExecutePythonScript")

for a in ACTOR_SUB.get_all_level_actors():
    if a and unreal.Name(TAG) in a.tags:
        ACTOR_SUB.destroy_actor(a)
        REPORT["cleared"] += 1

asset = unreal.load_asset(ARCH)
if asset is None:
    raise RuntimeError("arch not found at {}".format(ARCH))
lift = -asset.get_bounding_box().min.z * SCALE

for index, x in enumerate(STATION_X):
    actor = ACTOR_SUB.spawn_actor_from_object(
        asset, unreal.Vector(x, STATION_Y, lift), unreal.Rotator(0.0, 0.0, 0.0))
    if actor is None:
        continue
    actor.set_actor_scale3d(unreal.Vector(SCALE, SCALE, SCALE))
    actor.tags = [unreal.Name(TAG), unreal.Name("LB.Environment.VisualOnly"),
                  unreal.Name("LB.NotProcessWIP")]
    actor.set_actor_label("Paint_Gantry_{:02d}".format(index + 1))
    REPORT["placed"] += 1

LEVEL_SUB.save_current_level()
with io.open(OUT, "w", encoding="utf-8") as h:
    h.write(json.dumps(REPORT, indent=1))
unreal.log("LINE_BOSS_PAINT_GANTRY placed={} cleared={}".format(
    REPORT["placed"], REPORT["cleared"]))
