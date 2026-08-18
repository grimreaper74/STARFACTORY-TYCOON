"""Hang real Cairnwell doors on the six door-line carriers.

The door meshes' pivots were never measured, so this measures each door's
local bounds live and derives the actor Z that puts the door's top edge at
the carriers' hook height (216 cm). One door variant per carrier.

Idempotent via LB.Batch07b. Run with -ExecutePythonScript.
"""
import io
import json
import os

import unreal

TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
TAG = "LB.Batch07b"
OUT = os.environ.get("LB_DOORS_OUT", "C:/Temp/lb_door_hang.json")
DOOR_ROOT = ("/Game/LineBoss/Factory/OneFactory/v001/Vehicles/"
             "Cairnwell2040PanelModules_v001/Meshes/")
DOORS = ["SM_LB_C2040_DOOR_FRONT_LEFT_v001", "SM_LB_C2040_DOOR_FRONT_RIGHT_v001",
         "SM_LB_C2040_DOOR_REAR_LEFT_v001", "SM_LB_C2040_DOOR_REAR_RIGHT_v001"]
HOOK_Z = 216.0
CARRIER_X = [5200.0 + n * 500.0 for n in range(6)]
LINE_Y = 6800.0

LEVEL_SUB = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTOR_SUB = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
REPORT = {"doors": [], "cleared": 0}

if not LEVEL_SUB.load_level(TARGET):
    raise RuntimeError("could not load target map")
world = unreal.EditorLevelLibrary.get_editor_world()
if world is None or TARGET.rsplit("/", 1)[-1] != world.get_name():
    raise RuntimeError("wrong world; use -ExecutePythonScript")
for actor in ACTOR_SUB.get_all_level_actors():
    if actor and unreal.Name(TAG) in actor.tags:
        ACTOR_SUB.destroy_actor(actor)
        REPORT["cleared"] += 1

for n, cx in enumerate(CARRIER_X):
    name = DOORS[n % len(DOORS)]
    mesh = unreal.load_asset(DOOR_ROOT + name)
    if mesh is None:
        raise RuntimeError("missing door mesh " + name)
    bounds = mesh.get_bounding_box()
    z = HOOK_Z - bounds.max.z
    actor = ACTOR_SUB.spawn_actor_from_object(
        mesh, unreal.Vector(cx, LINE_Y + 6.0, z),
        unreal.Rotator(0.0, 90.0, 0.0))
    if actor is None:
        continue
    actor.tags = [unreal.Name(TAG), unreal.Name("LB.Environment.VisualOnly"),
                  unreal.Name("LB.NotProcessWIP")]
    actor.set_actor_label("Asm_DoorLine_" + name.split("DOOR_")[-1])
    REPORT["doors"].append({
        "mesh": name, "x": cx, "z": round(z, 1),
        "local_bounds": [round(bounds.min.z, 1), round(bounds.max.z, 1)]})

LEVEL_SUB.save_current_level()
with io.open(OUT, "w", encoding="utf-8") as handle:
    handle.write(json.dumps(REPORT, indent=1, sort_keys=True))
unreal.log("LINE_BOSS_DOOR_HANG {}".format(json.dumps(REPORT)))
