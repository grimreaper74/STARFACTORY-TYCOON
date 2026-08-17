"""Stand the candidate vendor kit in a grid so it can be photographed.

Placing 282 fabric actors from measured bounds produced a blue ribbon, brackets that
read as flags and racking that read as fencing - because bounds tell you pitch and
fit, not appearance. This puts one of each candidate on the empty paint bay floor at
a uniform spacing so a single overhead capture shows what the project actually owns.

Grid goes in the paint bay because it is nearly empty and the existing framing
fallback can already frame a bay by name, so no new camera tooling is needed.
Idempotent, and the caller is expected to clear it afterwards.

Run with -ExecutePythonScript.
"""
import io
import json
import os

import unreal

TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
TAG = "LB.ContactSheet"
OUT = os.environ.get("LB_SHEET_OUT", "C:/Temp/lb_sheet.json")

# Paint bay: centre (10000,-8500), size 22000 x 10000.
ORIGIN_X, ORIGIN_Y = 1000.0, -12000.0
PITCH = 2600.0
COLUMNS = 6

CANDIDATES = [
    "/Game/LineBoss/Vendor/FactoryEnvironment/Meshes/SM_IndustrialPlatform01",
    "/Game/Meshes/SM_IndustrialPlatform02",
    "/Game/Meshes/SM_IndustrialPlatform03",
    "/Game/Meshes/SM_PlatformGrill_01",
    "/Game/Meshes/SM_PlatformPillar_01",
    "/Game/LineBoss/Vendor/FactoryEnvironment/Meshes/SM_PlatformRailing_01",
    "/Game/Meshes/SM_FloorStairs01",
    "/Game/Meshes/SM_HeavyArch01",
    "/Game/Meshes/SM_HeavyArch02",
    "/Game/Meshes/SM_HeavyArch03",
    "/Game/Meshes/SM_LampArch01",
    "/Game/Meshes/SM_LargeWindowFramed",
    "/Game/Meshes/SM_StorageShelvesBottom01",
    "/Game/Meshes/SM_StorageShelvesMiddle01",
    "/Game/Meshes/SM_StorageShelvesTop01",
    "/Game/Meshes/SM_ElectricalPanel_01",
    "/Game/Meshes/SM_ElectricalSupply_Switchboard01",
    "/Game/Meshes/SM_ConcreteWall",
    "/Game/Meshes/SM_ConcretePillar01",
    "/Game/Meshes/SM_Container01_01",
    "/Game/Meshes/SM_FloorDrainage01",
    "/Game/Meshes/SM_AirConditioner01",
    "/Game/Meshes/SM_AssemblyLine01",
    "/Game/Meshes/SM_AssemblyLineControl01",
]

LEVEL_SUB = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTOR_SUB = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
REPORT = {"placed": [], "missing": [], "cleared": 0}

if not LEVEL_SUB.load_level(TARGET):
    raise RuntimeError("could not load target")
world = unreal.EditorLevelLibrary.get_editor_world()
if world is None or TARGET.rsplit("/", 1)[-1] != world.get_name():
    raise RuntimeError("wrong world; use -ExecutePythonScript")

for actor in ACTOR_SUB.get_all_level_actors():
    if actor and unreal.Name(TAG) in actor.tags:
        ACTOR_SUB.destroy_actor(actor)
        REPORT["cleared"] += 1

for index, path in enumerate(CANDIDATES):
    asset = unreal.load_asset(path)
    if asset is None:
        REPORT["missing"].append(path.rsplit("/", 1)[-1])
        continue
    column = index % COLUMNS
    row = index // COLUMNS
    # Sit each mesh on the slab: the vendor pack does not use floor pivots.
    lift = -asset.get_bounding_box().min.z
    actor = ACTOR_SUB.spawn_actor_from_object(
        asset,
        unreal.Vector(ORIGIN_X + column * PITCH, ORIGIN_Y + row * PITCH, lift),
        unreal.Rotator(0.0, 0.0, 0.0))
    if actor is None:
        REPORT["missing"].append(path.rsplit("/", 1)[-1])
        continue
    actor.tags = [unreal.Name(TAG), unreal.Name("LB.Environment.VisualOnly"),
                  unreal.Name("LB.NotProcessWIP")]
    actor.set_actor_label("SHEET_{:02d}_{}".format(
        index, path.rsplit("/", 1)[-1]))
    REPORT["placed"].append({"index": index,
                             "name": path.rsplit("/", 1)[-1],
                             "grid": [column, row]})

LEVEL_SUB.save_current_level()
with io.open(OUT, "w", encoding="utf-8") as handle:
    handle.write(json.dumps(REPORT, indent=1))
unreal.log("LINE_BOSS_CONTACT_SHEET placed {} missing {} cleared {} -> {}".format(
    len(REPORT["placed"]), len(REPORT["missing"]), REPORT["cleared"], OUT))
