"""First placement for the intake machines that were never in the map.

Two destack magazines, the cleaning dock and two cleaning robots stand
in the coil yard west of the press building, near the stands the coils
arrive on. Idempotent via LB.IntakeMachines. Run with
-ExecutePythonScript.
"""
import json

import unreal

TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
TAG = "LB.IntakeMachines"
OUT = "C:/Temp/lb_intake_machines.json"
DIR = "/Game/LineBoss/Candidates/PressShop/IntakeRework_v001/"

MESHES = {
    "magazine": DIR + "SM_LB_Press_DestackMagazine_v002",
    "dock": DIR + "SM_LB_Press_CleaningDock_v002",
    "robot": DIR + "SM_LB_Press_CleaningRobot_v002",
}

LEVEL_SUB = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTOR_SUB = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not LEVEL_SUB.load_level(TARGET):
    raise RuntimeError("could not load target map")

LOADED = {key: unreal.load_asset(path) for key, path in MESHES.items()}
for key, asset in LOADED.items():
    if asset is None:
        raise RuntimeError("missing " + MESHES[key])

REPORT = {"cleared": 0, "placed": 0}
for actor in list(ACTOR_SUB.get_all_level_actors()):
    if TAG in [str(t) for t in actor.tags]:
        ACTOR_SUB.destroy_actor(actor)
        REPORT["cleared"] += 1

def spawn(key, x, y, yaw):
    actor = ACTOR_SUB.spawn_actor_from_object(
        LOADED[key], unreal.Vector(x, y, 0.0),
        unreal.Rotator(0.0, 0.0, yaw))
    if actor is None:
        return
    REPORT["placed"] += 1
    actor.set_actor_label("Site_Intake_{:02d}".format(REPORT["placed"]))
    for tag in (TAG, "LB.Environment.VisualOnly", "LB.NotProcessWIP"):
        actor.tags.append(tag)

spawn("magazine", -26200.0, 5200.0, 0.0)
spawn("magazine", -26200.0, 6400.0, 0.0)
spawn("dock", -26400.0, 8200.0, 90.0)
spawn("robot", -25600.0, 8000.0, 35.0)
spawn("robot", -25900.0, 4300.0, 160.0)

if not LEVEL_SUB.save_current_level():
    raise RuntimeError("could not save the level")

with open(OUT, "w") as handle:
    json.dump(REPORT, handle, indent=1)
unreal.log("LINE_BOSS_INTAKE_MACHINES placed={}".format(REPORT["placed"]))
