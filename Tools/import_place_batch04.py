"""Batch 04: assembly test end, plus the booth robots get their spray tools.

Imports the applicator (palette-native slots) and three machines; places the
water test booth, rolls dyno and headlamp aim rig in the test zones; then
reconfigures the four Paint_Booth_* robots to ELBBodyShopToolType
SprayApplicator, which LoadCompleteArt now supports.

Idempotent via LB.Batch04. Run with -ExecutePythonScript.
"""
import io
import json
import os

import unreal

SRC = (r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8"
       r"/SourceAssets/Candidate")
TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
TAG = "LB.Batch04"
OUT = os.environ.get("LB_BATCH_OUT", "C:/Temp/lb_batch04.json")

MODELS = [
    ("PaintShop/SprayApplicator_v001", "SM_LB_Paint_SprayApplicatorTool_v001"),
    ("AssemblyShop/HeadlampAim_v001", "SM_LB_Assembly_HeadlampAimRig_v001"),
    ("AssemblyShop/RollsDyno_v001", "SM_LB_Assembly_RollsDynoBrakeTestBed_v001"),
    ("AssemblyShop/WaterTest_v001", "SM_LB_Assembly_WaterLeakTestBooth_v001"),
]
REPORT = {"imported": {}, "placed": {}, "cleared": 0, "retooled": []}
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


# Test end: water booth in the north-centre band, dyno at station 22,
# aim rig ahead of station 23.
place("SM_LB_Assembly_WaterLeakTestBooth_v001", 10000.0, 12900.0, 0.0,
      "Asm_WaterTest")
place("SM_LB_Assembly_RollsDynoBrakeTestBed_v001", 8400.0, 11500.0, 0.0,
      "Asm_RollsDyno_S22")
place("SM_LB_Assembly_HeadlampAimRig_v001", 6200.0, 11500.0, 0.0,
      "Asm_HeadlampAim_S23")

# Re-tool the four booth robots to the spray applicator.
ROLE = unreal.LBBodyShopRobotRole.PANEL_HANDLING
TOOL = unreal.LBBodyShopToolType.SPRAY_APPLICATOR
for actor in ACTOR_SUB.get_all_level_actors():
    if actor is None or not actor.get_actor_label().startswith("Paint_Booth_"):
        continue
    if not isinstance(actor, unreal.LBBodyShopRobotActor):
        continue
    label = actor.get_actor_label()
    slot = unreal.LBBodyShopRobotSlotDefinition()
    slot.set_editor_property("slot_id", unreal.Name(label + "_Slot"))
    slot.set_editor_property("allowed_roles", [ROLE])
    slot.set_editor_property("allowed_tools", [TOOL])
    assign = unreal.LBBodyShopRobotAssignment()
    assign.set_editor_property("slot_id", unreal.Name(label + "_Slot"))
    assign.set_editor_property("role", ROLE)
    assign.set_editor_property("tool", TOOL)
    assign.set_editor_property("enabled", True)
    assign.set_editor_property("condition01", 1.0)
    actor.configure_for_authored_slot(unreal.Name("PaintBooth"), slot, assign)
    actor.set_authored_pose(unreal.LBBodyShopRobotPose.PROCESS, True)
    REPORT["retooled"].append(
        {"label": label, "ok": bool(actor.has_complete_art_presentation())})

LEVEL_SUB.save_current_level()
REPORT["total"] = sum(REPORT["placed"].values())
with io.open(OUT, "w", encoding="utf-8") as h:
    h.write(json.dumps(REPORT, indent=1, sort_keys=True))
unreal.log("LINE_BOSS_BATCH04 {}".format(json.dumps(REPORT, sort_keys=True)))
