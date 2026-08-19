"""Batch 15: the weld quality-and-handoff kit - stud feeders at P15, BIW
buffer racks and rework booths at P17, closure door fixtures in the
quality corner, and the P18 handoff (skid lift transfers + overhead drop
lift) toward paint.

Idempotent via LB.Batch15. Run with -ExecutePythonScript.
"""
import io
import json
import os

import unreal

SRC = (r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8"
       r"/SourceAssets/Candidate")
TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
TAG = "LB.Batch15"
OUT = os.environ.get("LB_BATCH_OUT", "C:/Temp/lb_batch15.json")

MODELS = [
    ("WeldShop/StudFeeder_v001", "SM_LB_Weld_StudFeeder_v001"),
    ("WeldShop/BIWBufferRack_v001", "SM_LB_Weld_BIWBufferRack_v001"),
    ("WeldShop/ReworkBoothFrame_v001", "SM_LB_Weld_ReworkBoothFrame_v001"),
    ("WeldShop/ClosureDoorFixture_v001", "SM_LB_Weld_ClosureDoorFixture_v001"),
    ("WeldShop/SkidLiftTransfer_v001", "SM_LB_Weld_SkidLiftTransfer_v001"),
    ("WeldShop/OverheadDropLift_v001", "SM_LB_Weld_OverheadDropLift_v001"),
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
    size = mesh.get_bounding_box().max - mesh.get_bounding_box().min
    REPORT["imported"][name] = [round(size.x, 1), round(size.y, 1),
                                round(size.z, 1)]
    MESHES[name] = mesh

LEVEL_SUB = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTOR_SUB = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not LEVEL_SUB.load_level(TARGET):
    raise RuntimeError("could not load target map")
w = unreal.EditorLevelLibrary.get_editor_world()
if w is None or TARGET.rsplit("/", 1)[-1] != w.get_name():
    raise RuntimeError("wrong world; use -ExecutePythonScript")
for a in ACTOR_SUB.get_all_level_actors():
    if a and unreal.Name(TAG) in a.tags:
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


# Stud feeders flanking P15, hose stands toward the line.
place("SM_LB_Weld_StudFeeder_v001", -9500.0, -12300.0, 90.0,
      "Weld_StudFeeder_A")
place("SM_LB_Weld_StudFeeder_v001", -8600.0, -12300.0, 90.0,
      "Weld_StudFeeder_B")
# BIW buffer racks in the P17 south band.
for n, rx in enumerate((-5900.0, -5050.0, -4200.0)):
    place("SM_LB_Weld_BIWBufferRack_v001", rx, -12500.0, 0.0,
          "Weld_BIWBuffer_{:d}".format(n))
# Rework booths north of P17, curtained fronts facing the line.
place("SM_LB_Weld_ReworkBoothFrame_v001", -5500.0, -9900.0, 0.0,
      "Weld_ReworkBooth_A")
place("SM_LB_Weld_ReworkBoothFrame_v001", -4400.0, -9900.0, 0.0,
      "Weld_ReworkBooth_B")
# Closure door fixtures in the west quality corner, faces east.
place("SM_LB_Weld_ClosureDoorFixture_v001", -19250.0, -8100.0, 90.0,
      "Weld_DoorFixture_A")
place("SM_LB_Weld_ClosureDoorFixture_v001", -19250.0, -8600.0, 90.0,
      "Weld_DoorFixture_B")
# P18 handoff toward paint: two lift transfers and the portal drop lift.
place("SM_LB_Weld_SkidLiftTransfer_v001", -2350.0, -11200.0, 0.0,
      "Weld_SkidTransfer_A")
place("SM_LB_Weld_SkidLiftTransfer_v001", -1600.0, -11200.0, 0.0,
      "Weld_SkidTransfer_B")
place("SM_LB_Weld_OverheadDropLift_v001", -1150.0, -11200.0, 90.0,
      "Weld_DropLift")

LEVEL_SUB.save_current_level()
REPORT["total"] = sum(REPORT["placed"].values())
with io.open(OUT, "w", encoding="utf-8") as h:
    h.write(json.dumps(REPORT, indent=1, sort_keys=True))
unreal.log("LINE_BOSS_BATCH15 {}".format(json.dumps(REPORT, sort_keys=True)))
