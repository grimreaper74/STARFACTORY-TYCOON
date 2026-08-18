"""Batch 01: import the six authored machines and place them in the map in one pass.

Owner's workflow: author in a batch, check in Unreal in a batch. Placements follow the
plant plan - welders and cell hardware inside weld's fenced cells, booths in paint's
empty east half (NOT over the frozen paint presentation's stations), marriage v003
replacing the failed v001 at assembly position 12.

Idempotent: clears LB.Batch01 and the old LB.Assembly.Marriage tag first.
Run with -ExecutePythonScript.
"""
import io
import json
import os

import unreal

SRC = (r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8"
       r"/SourceAssets/Candidate")
TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
TAG = "LB.Batch01"
OUT = os.environ.get("LB_BATCH_OUT", "C:/Temp/lb_batch01.json")

MODELS = [
    ("AssemblyShop/PowertrainMarriage_v003", "SM_LB_Assembly_PowertrainMarriage_v003"),
    ("WeldShop/PedestalWelder_v001", "SM_LB_Weld_PedestalWelder_v001"),
    ("WeldShop/TipDresser_v001", "SM_LB_Weld_TipDresser_v001"),
    ("WeldShop/GeoPinUnit_v001", "SM_LB_Weld_GeoPinUnit_v001"),
    ("WeldShop/ClampUnit_v001", "SM_LB_Weld_ClampUnit_v001"),
    ("PaintShop/SprayBoothShell_v001", "SM_LB_Paint_SprayBoothShell_v001"),
]

REPORT = {"imported": {}, "placed": {}, "cleared": 0}
tools = unreal.AssetToolsHelpers.get_asset_tools()
tasks = []
for folder, name in MODELS:
    options = unreal.FbxImportUI()
    options.set_editor_property("import_mesh", True)
    options.set_editor_property("import_materials", False)
    options.set_editor_property("import_textures", False)
    options.set_editor_property("import_as_skeletal", False)
    options.static_mesh_import_data.set_editor_property("combine_meshes", True)
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", os.path.join(SRC, folder, name + ".fbx"))
    task.set_editor_property("destination_path",
                             "/Game/LineBoss/Candidates/" + folder)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", True)
    task.set_editor_property("options", options)
    tasks.append(task)
tools.import_asset_tasks(tasks)

MESHES = {}
for (folder, name), task in zip(MODELS, tasks):
    paths = list(task.get_editor_property("imported_object_paths") or [])
    if not paths:
        raise RuntimeError("import produced nothing for {}".format(name))
    mesh = unreal.load_asset(paths[0].split(".")[0])
    if mesh is None:
        raise RuntimeError("could not load {}".format(paths[0]))
    size = mesh.get_bounding_box().max - mesh.get_bounding_box().min
    REPORT["imported"][name] = [round(size.x, 1), round(size.y, 1), round(size.z, 1)]
    MESHES[name] = mesh

LEVEL_SUB = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTOR_SUB = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not LEVEL_SUB.load_level(TARGET):
    raise RuntimeError("could not load target map")
w = unreal.EditorLevelLibrary.get_editor_world()
if w is None or TARGET.rsplit("/", 1)[-1] != w.get_name():
    raise RuntimeError("wrong world; use -ExecutePythonScript")
for a in ACTOR_SUB.get_all_level_actors():
    if a and (unreal.Name(TAG) in a.tags
              or unreal.Name("LB.Assembly.Marriage") in a.tags):
        ACTOR_SUB.destroy_actor(a)
        REPORT["cleared"] += 1


def place(name, x, y, yaw=0.0, label=None):
    actor = ACTOR_SUB.spawn_actor_from_object(
        MESHES[name], unreal.Vector(x, y, 0.0), unreal.Rotator(0.0, yaw, 0.0))
    if actor is None:
        return
    actor.tags = [unreal.Name(TAG), unreal.Name("LB.Environment.VisualOnly"),
                  unreal.Name("LB.NotProcessWIP")]
    if label:
        actor.set_actor_label(label)
    key = name.rsplit("_", 2)[0]
    REPORT["placed"][key] = REPORT["placed"].get(key, 0) + 1


WELD_A = [(-3050.0 - n * 2000.0, -7000.0) for n in range(9)]
WELD_B = [(-19050.0 + n * 2000.0, -11200.0) for n in range(9)]

# Marriage station replaces the failed v001 at assembly position 12.
place("SM_LB_Assembly_PowertrainMarriage_v003", 28200.0, 5500.0, 0.0,
      "Assembly_PowertrainMarriage_Pos12")

# Pedestal welders inside the fenced cells, four per run between stations.
for n, x in enumerate((-5050.0, -9050.0, -13050.0, -17050.0)):
    place("SM_LB_Weld_PedestalWelder_v001", x, -5750.0, 180.0)
    place("SM_LB_Weld_PedestalWelder_v001", x, -12450.0, 0.0)

# A tip dresser beside every station; clamps on the pad corners; pins on the face.
for sx, sy in WELD_A + WELD_B:
    place("SM_LB_Weld_TipDresser_v001", sx + 650.0, sy + 850.0, 225.0)
    for cx in (-1.0, 1.0):
        for cy in (-1.0, 1.0):
            place("SM_LB_Weld_ClampUnit_v001", sx + cx * 500.0, sy + cy * 650.0,
                  90.0 * cy)
    for n in range(3):
        place("SM_LB_Weld_GeoPinUnit_v001", sx - 300.0 + n * 300.0, sy - 750.0)

# Two booths in paint's empty east half - clear of the frozen presentation.
place("SM_LB_Paint_SprayBoothShell_v001", 14500.0, -8500.0, 0.0, "Paint_Booth_E1")
place("SM_LB_Paint_SprayBoothShell_v001", 18200.0, -8500.0, 0.0, "Paint_Booth_E2")

LEVEL_SUB.save_current_level()
REPORT["total"] = sum(REPORT["placed"].values())
with io.open(OUT, "w", encoding="utf-8") as h:
    h.write(json.dumps(REPORT, indent=1))
unreal.log("LINE_BOSS_BATCH01 {}".format(json.dumps(REPORT)))
