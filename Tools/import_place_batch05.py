"""Batch 05: lay the paint ED process line - Task 32's spine.

Six 18 m dip tanks, a 9 m drain gap, then twelve 6 m oven segments along the
paint bay's north band (y -5300); PF track goalposts chain over the tank run
(the oven carries the line in its own roof slot); eight carriers ride the
track with four painted-body shells hung mid-process. All well clear of the
frozen 119-instance station presentation at y -8500 and the booths.

Idempotent via LB.Batch05. Run with -ExecutePythonScript.
"""
import io
import json
import os

import unreal

SRC = (r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8"
       r"/SourceAssets/Candidate")
TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
TAG = "LB.Batch05"
OUT = os.environ.get("LB_BATCH_OUT", "C:/Temp/lb_batch05.json")
BODY = ("/Game/LineBoss/Factory/OneFactory/v001/Vehicles/"
        "Cairnwell2040Runtime_v001/Meshes/"
        "SM_LB_C2040_EmeraldBodyVisualAuthority_v001")

MODELS = [
    ("PaintShop/EDDipTank_v001", "SM_LB_Paint_EDDipTank_v001"),
    ("PaintShop/PFCarrier_v001", "SM_LB_Paint_PFCarrier_v001"),
    ("PaintShop/PFTrack_v001", "SM_LB_Paint_PFTrackSegment_v001"),
    ("PaintShop/OvenSegment_v003", "SM_LB_Paint_OvenSegment_v003"),
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
body_mesh = unreal.load_asset(BODY)
if body_mesh is None:
    raise RuntimeError("missing painted body mesh")
MESHES["Body"] = body_mesh

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


def place(name, x, y, z=0.0, yaw=0.0, label=None):
    actor = ACTOR_SUB.spawn_actor_from_object(
        MESHES[name], unreal.Vector(x, y, z), unreal.Rotator(0.0, yaw, 0.0))
    if actor is None:
        return
    actor.tags = [unreal.Name(TAG), unreal.Name("LB.Environment.VisualOnly"),
                  unreal.Name("LB.NotProcessWIP")]
    if label:
        actor.set_actor_label(label)
    key = label.rsplit("_", 1)[0] if label else name
    REPORT["placed"][key] = REPORT["placed"].get(key, 0) + 1


ED_Y = -5300.0

# Six dip tanks: pretreatment stages then the ED tank itself.
for n in range(6):
    place("SM_LB_Paint_EDDipTank_v001", 1500.0 + n * 1900.0, ED_Y, 0.0, 0.0,
          "Paint_EDTank_{:02d}".format(n))
# PF track over the tank run and the drain gap.
for n in range(32):
    place("SM_LB_Paint_PFTrackSegment_v001", 400.0 + n * 400.0, ED_Y, 0.0,
          0.0, "Paint_PFTrack_{:02d}".format(n))
# Twelve oven segments carry the line onward in their roof slot.
for n in range(12):
    place("SM_LB_Paint_OvenSegment_v003", 13400.0 + n * 600.0, ED_Y, 0.0,
          0.0, "Paint_Oven_{:02d}".format(n))
# Carriers along the tank run; four carry painted shells mid-process.
CARRIERS = (700.0, 1500.0, 3400.0, 5300.0, 7200.0, 9100.0, 11000.0, 12200.0)
for n, cx in enumerate(CARRIERS):
    place("SM_LB_Paint_PFCarrier_v001", cx, ED_Y, 0.0, 0.0,
          "Paint_PFCarrier_{:02d}".format(n))
for cx in (3400.0, 7200.0, 11000.0, 12200.0):
    place("Body", cx, ED_Y, 320.0, 0.0, "Paint_HungBody")

LEVEL_SUB.save_current_level()
REPORT["total"] = sum(REPORT["placed"].values())
with io.open(OUT, "w", encoding="utf-8") as h:
    h.write(json.dumps(REPORT, indent=1, sort_keys=True))
unreal.log("LINE_BOSS_BATCH05 {}".format(json.dumps(REPORT, sort_keys=True)))
