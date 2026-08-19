"""Batch 13: weld quality area (CMM, finish bench, gun stands) and the ED
rectifier row.

Idempotent via LB.Batch13. Run with -ExecutePythonScript.
"""
import io
import json
import os

import unreal

SRC = (r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8"
       r"/SourceAssets/Candidate")
TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
TAG = "LB.Batch13"
OUT = os.environ.get("LB_BATCH_OUT", "C:/Temp/lb_batch13.json")

MODELS = [
    ("WeldShop/CMMBed_v001", "SM_LB_Weld_CMMBed_v001"),
    ("WeldShop/MetalFinishBench_v001", "SM_LB_Weld_MetalFinishBench_v001"),
    ("WeldShop/RespotGunStand_v001", "SM_LB_Weld_RespotGunStand_v001"),
    ("PaintShop/Rectifier_v001", "SM_LB_Paint_RectifierCabinet_v001"),
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


place("SM_LB_Weld_CMMBed_v001", -19200.0, -9100.0, 0.0, "Weld_CMM")
place("SM_LB_Weld_MetalFinishBench_v001", -19200.0, -7700.0, 0.0,
      "Weld_FinishBench")
place("SM_LB_Weld_RespotGunStand_v001", -8950.0, -6300.0, 0.0,
      "Weld_GunStand_A")
place("SM_LB_Weld_RespotGunStand_v001", -13150.0, -11900.0, 180.0,
      "Weld_GunStand_B")
for n, rx in enumerate((2500.0, 6300.0, 10100.0)):
    place("SM_LB_Paint_RectifierCabinet_v001", rx, -4600.0, -90.0,
          "Paint_Rectifier_{:d}".format(n))

LEVEL_SUB.save_current_level()
REPORT["total"] = sum(REPORT["placed"].values())
with io.open(OUT, "w", encoding="utf-8") as h:
    h.write(json.dumps(REPORT, indent=1, sort_keys=True))
unreal.log("LINE_BOSS_BATCH13 {}".format(json.dumps(REPORT, sort_keys=True)))
