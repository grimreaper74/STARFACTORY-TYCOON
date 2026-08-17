"""Stand a lit gantry arch over each of assembly's 24 stations.

Same pattern verified in weld: SM_LampArch01 at 1.6x scale. The arch spans 788 cm in Y
natively, and assembly's runs travel along X, so it already straddles them - no
rotation. 1.6x is not cosmetic: at native 588 cm the arch is shorter than the 650 cm
station envelope and would clip through the machine it spans.

Positions from CanonicalLocation in LBOneFactoryAssemblyStarterLayout.cpp:143 - two
runs of 12 at 2200 cm pitch, trim/chassis at Y 5500 running east, final at Y 11500
running back west.

Idempotent. Run with -ExecutePythonScript.
"""
import io
import json
import os

import unreal

TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
TAG = "LB.Assembly.Gantry"
ARCH = "/Game/Meshes/SM_LampArch01"
SCALE = 1.6
OUT = os.environ.get("LB_GANTRY_OUT", "C:/Temp/lb_gantry.json")

STATIONS = [(4000.0 + n * 2200.0, 5500.0) for n in range(12)]
STATIONS += [(28200.0 - n * 2200.0, 11500.0) for n in range(12)]

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

for index, (x, y) in enumerate(STATIONS):
    actor = ACTOR_SUB.spawn_actor_from_object(
        asset, unreal.Vector(x, y, lift), unreal.Rotator(0.0, 0.0, 0.0))
    if actor is None:
        continue
    actor.set_actor_scale3d(unreal.Vector(SCALE, SCALE, SCALE))
    actor.tags = [unreal.Name(TAG), unreal.Name("LB.Environment.VisualOnly"),
                  unreal.Name("LB.NotProcessWIP")]
    actor.set_actor_label("Assembly_Gantry_{:02d}".format(index + 1))
    REPORT["placed"] += 1

LEVEL_SUB.save_current_level()
with io.open(OUT, "w", encoding="utf-8") as h:
    h.write(json.dumps(REPORT, indent=1))
unreal.log("LINE_BOSS_ASSEMBLY_GANTRY placed={} cleared={}".format(
    REPORT["placed"], REPORT["cleared"]))
