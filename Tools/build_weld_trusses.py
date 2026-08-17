"""Roof weld with the authored 40 m wide-span truss press already uses.

SM_CA_MW_PressShop_WideSpanTruss_40m_TBC_v372 is Codex's own shop-scale steelwork. It
was wrongly listed as missing (as SM_LB_Weld_ShopGantry_18000_v001); it exists, is at
the right scale, and is already proven in the shop the owner approves of.

The grid copies press's own pattern rather than inventing one, read straight off its 12
placements: 40 m spans at 4000 cm pitch in X, rows every 1500 cm in Y, Z 1740, zero
rotation, and **scale 100** - the mesh is authored small, so a native-scale placement
would be invisible.

Z 1740 sits above the 900 cm roof-hide threshold, so the camera cutaway correctly
takes these out of an overhead view.

Idempotent. Run with -ExecutePythonScript.
"""
import io
import json
import os

import unreal

TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
TAG = "LB.Weld.Truss"
# Path read from the reference dump, not guessed - my first attempt invented a
# plausible-looking PressTrains path and the load failed.
TRUSS = ("/Game/LineBoss/Candidates/PressShop/Structure/WideSpanTruss_v373/"
         "SM_CA_MW_PressShop_WideSpanTruss_40m_TBC_v372")
OUT = os.environ.get("LB_TRUSS_OUT", "C:/Temp/lb_truss.json")

SCALE = 100.0
Z = 1740.0
X_CENTRES = [-18000.0, -14000.0, -10000.0, -6000.0]
Y_ROWS = [-12750.0, -11250.0, -9750.0, -8250.0, -6750.0, -5250.0]

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

asset = unreal.load_asset(TRUSS)
if asset is None:
    raise RuntimeError("truss not found at {}".format(TRUSS))

for x in X_CENTRES:
    for y in Y_ROWS:
        actor = ACTOR_SUB.spawn_actor_from_object(
            asset, unreal.Vector(x, y, Z), unreal.Rotator(0.0, 0.0, 0.0))
        if actor is None:
            continue
        actor.set_actor_scale3d(unreal.Vector(SCALE, SCALE, SCALE))
        actor.tags = [unreal.Name(TAG), unreal.Name("LB.Environment.VisualOnly"),
                      unreal.Name("LB.NotProcessWIP")]
        actor.set_actor_label("Weld_Truss_{:.0f}_{:.0f}".format(x, y))
        REPORT["placed"] += 1

LEVEL_SUB.save_current_level()
with io.open(OUT, "w", encoding="utf-8") as h:
    h.write(json.dumps(REPORT, indent=1))
unreal.log("LINE_BOSS_WELD_TRUSS placed {} cleared {} -> {}".format(
    REPORT["placed"], REPORT["cleared"], OUT))
