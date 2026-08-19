"""Batch 16: the last named paint pieces - burner houses beside the oven
band, the tack-off tunnel before booth 1, polish decks flanking the line
after the flash-offs, and the carrier turntable at the east fold.

Idempotent via LB.Batch16. Run with -ExecutePythonScript.
"""
import io
import json
import os

import unreal

SRC = (r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8"
       r"/SourceAssets/Candidate")
TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
TAG = "LB.Batch16"
OUT = os.environ.get("LB_BATCH_OUT", "C:/Temp/lb_batch16.json")

MODELS = [
    ("PaintShop/OvenBurnerHouse_v001", "SM_LB_Paint_OvenBurnerHouse_v001"),
    ("PaintShop/TackOffTunnel_v001", "SM_LB_Paint_TackOffTunnel_v001"),
    ("PaintShop/PolishDeck_v001", "SM_LB_Paint_PolishDeck_v001"),
    ("PaintShop/CarrierTurntable_v001", "SM_LB_Paint_CarrierTurntable_v001"),
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


# Burner houses beside the oven band, duct runs facing the oven.
place("SM_LB_Paint_OvenBurnerHouse_v001", 14600.0, -4650.0, 0.0,
      "Paint_BurnerHouse_A")
place("SM_LB_Paint_OvenBurnerHouse_v001", 18400.0, -4650.0, 0.0,
      "Paint_BurnerHouse_B")
# Tack-off tunnel in the gap between the sealer decks and booth 1.
place("SM_LB_Paint_TackOffTunnel_v001", 13900.0, -8500.0, 0.0,
      "Paint_TackOffTunnel")
# Polish decks flanking the line after the flash-offs, lamps toward it.
place("SM_LB_Paint_PolishDeck_v001", 20200.0, -7600.0, 0.0,
      "Paint_PolishDeck_N")
place("SM_LB_Paint_PolishDeck_v001", 20200.0, -9400.0, 180.0,
      "Paint_PolishDeck_S")
# Carrier turntable at the east serpentine fold of the ED lane.
place("SM_LB_Paint_CarrierTurntable_v001", 20800.0, -5300.0, 0.0,
      "Paint_CarrierTurntable")

LEVEL_SUB.save_current_level()
REPORT["total"] = sum(REPORT["placed"].values())
with io.open(OUT, "w", encoding="utf-8") as h:
    h.write(json.dumps(REPORT, indent=1, sort_keys=True))
unreal.log("LINE_BOSS_BATCH16 {}".format(json.dumps(REPORT, sort_keys=True)))
