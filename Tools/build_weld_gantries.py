"""Stand a lit gantry arch over each of weld's 18 stations.

The only dressing item proven usable by the rendered contact sheet. SM_LampArch01 is
a genuine slender lit arch with a lamp head, unlike SM_HeavyArch01 which renders as a
bracket. Measured native size 121 x 788 x 588 cm: it already spans Y, which is across
a line running along X, so no rotation is needed.

Scaled 1.6x. At native height the 588 cm arch is SHORTER than the 650 cm station
envelope and would clip through the machine it is meant to span; 1.6x gives 941 cm of
clearance and a 12.6 m span, which is right for a gantry over a cell.

Station positions come from CanonicalLocation in LBOneFactoryBodyWeldStarterLayout.cpp
as re-laid on the east-opening serpentine: 2000 cm pitch, run A at Y -7000 from
X -3050 westward, run B at Y -11200 from X -19050 eastward.

Idempotent. Run with -ExecutePythonScript.
"""
import io
import json
import os

import unreal

TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
TAG = "LB.Weld.Gantry"
ARCH = "/Game/Meshes/SM_LampArch01"
SCALE = 1.6
OUT = os.environ.get("LB_GANTRY_OUT", "C:/Temp/lb_gantry.json")

LEVEL_SUB = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTOR_SUB = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
REPORT = {"placed": 0, "cleared": 0, "positions": []}

if not LEVEL_SUB.load_level(TARGET):
    raise RuntimeError("could not load target")
world = unreal.EditorLevelLibrary.get_editor_world()
if world is None or TARGET.rsplit("/", 1)[-1] != world.get_name():
    raise RuntimeError("wrong world; use -ExecutePythonScript")

for actor in ACTOR_SUB.get_all_level_actors():
    if actor and unreal.Name(TAG) in actor.tags:
        ACTOR_SUB.destroy_actor(actor)
        REPORT["cleared"] += 1

asset = unreal.load_asset(ARCH)
if asset is None:
    raise RuntimeError("missing {}".format(ARCH))
lift = -asset.get_bounding_box().min.z * SCALE

STATIONS = [(-3050.0 - n * 2000.0, -7000.0) for n in range(9)]
STATIONS += [(-19050.0 + n * 2000.0, -11200.0) for n in range(9)]

for index, (x, y) in enumerate(STATIONS):
    actor = ACTOR_SUB.spawn_actor_from_object(
        asset, unreal.Vector(x, y, lift), unreal.Rotator(0.0, 0.0, 0.0))
    if actor is None:
        continue
    actor.set_actor_scale3d(unreal.Vector(SCALE, SCALE, SCALE))
    actor.tags = [unreal.Name(TAG), unreal.Name("LB.Environment.VisualOnly"),
                  unreal.Name("LB.NotProcessWIP")]
    actor.set_actor_label("Weld_Gantry_{:02d}".format(index + 1))
    REPORT["placed"] += 1
    REPORT["positions"].append([x, y])

LEVEL_SUB.save_current_level()
with io.open(OUT, "w", encoding="utf-8") as handle:
    handle.write(json.dumps(REPORT, indent=1))
unreal.log("LINE_BOSS_WELD_GANTRY placed {} cleared {} scale {} -> {}".format(
    REPORT["placed"], REPORT["cleared"], SCALE, OUT))
