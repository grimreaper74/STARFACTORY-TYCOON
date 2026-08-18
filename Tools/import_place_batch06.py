"""Batch 06: glazing cell kit, staging modules and authored marshalling racks.

A-frames and the urethane pump join the glazing robots at assembly station 7;
cockpit and HVAC modules stage at their trim stations; six authored
marshalling racks take the east half of weld's receiving lane (the west half
keeps the vendor shelving already placed).

Idempotent via LB.Batch06. Run with -ExecutePythonScript.
"""
import io
import json
import os

import unreal

SRC = (r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8"
       r"/SourceAssets/Candidate")
TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
TAG = "LB.Batch06"
OUT = os.environ.get("LB_BATCH_OUT", "C:/Temp/lb_batch06.json")

MODELS = [
    ("AssemblyShop/GlassAFrame_v001", "SM_LB_Assembly_GlassAFrameRack_v001"),
    ("AssemblyShop/UrethanePump_v001", "SM_LB_Assembly_UrethanePumpUnit_v001"),
    ("AssemblyShop/CockpitModule_v001", "SM_LB_Assembly_CockpitModule_v001"),
    ("AssemblyShop/HVACModule_v001", "SM_LB_Assembly_HVACModule_v001"),
    ("WeldShop/MarshallingRack_v001", "SM_LB_Weld_MarshallingRack_v001"),
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


# Glazing cell at assembly station 7.
place("SM_LB_Assembly_GlassAFrameRack_v001", 16800.0, 6400.0, 0.0,
      "Asm_GlassRack_W")
place("SM_LB_Assembly_GlassAFrameRack_v001", 17600.0, 6400.0, 0.0,
      "Asm_GlassRack_E")
place("SM_LB_Assembly_UrethanePumpUnit_v001", 16000.0, 6350.0, 90.0,
      "Asm_UrethanePump")
# Cockpits staged at station 5, HVAC at station 4.
for n in range(3):
    place("SM_LB_Assembly_CockpitModule_v001", 12300.0 + n * 500.0, 6400.0,
          180.0, "Asm_CockpitStage")
for n in range(4):
    place("SM_LB_Assembly_HVACModule_v001", 10100.0 + n * 300.0, 6400.0,
          180.0, "Asm_HVACStage")
# Authored marshalling racks in weld's east receiving lane.
for n in range(6):
    place("SM_LB_Weld_MarshallingRack_v001", -8500.0 + n * 320.0, -4400.0,
          0.0, "Weld_MarshRack")

LEVEL_SUB.save_current_level()
REPORT["total"] = sum(REPORT["placed"].values())
with io.open(OUT, "w", encoding="utf-8") as h:
    h.write(json.dumps(REPORT, indent=1, sort_keys=True))
unreal.log("LINE_BOSS_BATCH06 {}".format(json.dumps(REPORT, sort_keys=True)))
