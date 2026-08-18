"""Batch 07: the door line and painted-body store corner of assembly.

Lowerator feeding station 1, two store bays with four banked painted
shells on their deck rails, and the door sub-line: eight overhead track
segments with six door carriers over the door-off strip.

Idempotent via LB.Batch07. Run with -ExecutePythonScript.
"""
import io
import json
import os

import unreal

SRC = (r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8"
       r"/SourceAssets/Candidate")
TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
TAG = "LB.Batch07"
OUT = os.environ.get("LB_BATCH_OUT", "C:/Temp/lb_batch07.json")
BODY = ("/Game/LineBoss/Factory/OneFactory/v001/Vehicles/"
        "Cairnwell2040Runtime_v001/Meshes/"
        "SM_LB_C2040_EmeraldBodyVisualAuthority_v001")
TRACK = ("/Game/LineBoss/Candidates/AssemblyShop/OverheadTrack_v001/"
         "SM_LB_Assembly_OverheadTrackSegment_v001")

MODELS = [
    ("AssemblyShop/DoorCarrier_v001", "SM_LB_Assembly_DoorCarrier_v001"),
    ("AssemblyShop/BodyLowerator_v001", "SM_LB_Assembly_BodyLowerator_v001"),
    ("AssemblyShop/StoreBay_v001", "SM_LB_Assembly_StoreBay_v001"),
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
for key, path in (("Body", BODY), ("Track", TRACK)):
    asset = unreal.load_asset(path)
    if asset is None:
        raise RuntimeError("missing " + key)
    MESHES[key] = asset

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


place("SM_LB_Assembly_BodyLowerator_v001", 4300.0, 4400.0, 0.0, 0.0,
      "Asm_Lowerator")
for n, bx in enumerate((6500.0, 11500.0)):
    place("SM_LB_Assembly_StoreBay_v001", bx, 4300.0, 0.0, 0.0,
          "Asm_StoreBay_{:d}".format(n))
# Banked painted shells on the deck rails: two low, two high.
place("Body", 6500.0, 4190.0, 67.0, 0.0, "Asm_StoredBody")
place("Body", 6500.0, 4410.0, 287.0, 0.0, "Asm_StoredBody")
place("Body", 11500.0, 4190.0, 287.0, 0.0, "Asm_StoredBody")
place("Body", 11500.0, 4410.0, 67.0, 0.0, "Asm_StoredBody")
# Door sub-line: track over the door-off strip with six carriers.
for n in range(8):
    place("Track", 5000.0 + n * 400.0, 6800.0, 0.0, 0.0, "Asm_DoorTrack")
for n in range(6):
    place("SM_LB_Assembly_DoorCarrier_v001", 5200.0 + n * 500.0, 6800.0, 0.0,
          0.0, "Asm_DoorCarrier")

LEVEL_SUB.save_current_level()
REPORT["total"] = sum(REPORT["placed"].values())
with io.open(OUT, "w", encoding="utf-8") as h:
    h.write(json.dumps(REPORT, indent=1, sort_keys=True))
unreal.log("LINE_BOSS_BATCH07 {}".format(json.dumps(REPORT, sort_keys=True)))
