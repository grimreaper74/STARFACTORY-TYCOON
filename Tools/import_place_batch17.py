"""Batch 17: the audited tail placed - hemming cell with roller-hem
robots, water chillers, booth scrubber trenches, sealer robots at the
sealer decks, PF drive and switch in the ED run, sander decks before
tack-off.

Idempotent via LB.Batch17. Run with -ExecutePythonScript.
"""
import io
import json
import os

import unreal

SRC = (r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8"
       r"/SourceAssets/Candidate")
TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
TAG = "LB.Batch17"
OUT = os.environ.get("LB_BATCH_OUT", "C:/Temp/lb_batch17.json")

MODELS = [
    ("WeldShop/HemmingPress_v001", "SM_LB_Weld_HemmingPress_v001"),
    ("WeldShop/RollerHemTool_v001", "SM_LB_Weld_RollerHemTool_v001"),
    ("WeldShop/WaterChillerSkid_v001", "SM_LB_Weld_WaterChillerSkid_v001"),
    ("PaintShop/BoothScrubberTrench_v001",
     "SM_LB_Paint_BoothScrubberTrench_v001"),
    ("PaintShop/SealerNozzleTool_v001", "SM_LB_Paint_SealerNozzleTool_v001"),
    ("PaintShop/PFDrive_v001", "SM_LB_Paint_PFDrive_v001"),
    ("PaintShop/PFSwitch_v001", "SM_LB_Paint_PFSwitch_v001"),
    ("PaintShop/SanderDeck_v001", "SM_LB_Paint_SanderDeck_v001"),
]
REPORT = {"imported": {}, "placed": {}, "cleared": 0, "robots": []}
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


# Weld closures: hemming presses mid-gap between run A stations, throats
# toward the line.
place("SM_LB_Weld_HemmingPress_v001", -8050.0, -6300.0, 0.0, "Weld_Hemmer_A")
place("SM_LB_Weld_HemmingPress_v001", -6050.0, -6300.0, 0.0, "Weld_Hemmer_B")
# Weld services: water chiller skids on the north strip.
place("SM_LB_Weld_WaterChillerSkid_v001", -4500.0, -4400.0, 0.0,
      "Weld_Chiller_A")
place("SM_LB_Weld_WaterChillerSkid_v001", -3500.0, -4400.0, 0.0,
      "Weld_Chiller_B")
# Paint booths: scrubber trenches south of each booth, baffles toward it.
place("SM_LB_Paint_BoothScrubberTrench_v001", 14500.0, -9600.0, 0.0,
      "Paint_Scrubber_Booth1")
place("SM_LB_Paint_BoothScrubberTrench_v001", 18200.0, -9600.0, 0.0,
      "Paint_Scrubber_Booth2")
# ED run: switch at the head of the line, drive at the oven entry.
place("SM_LB_Paint_PFSwitch_v001", 0.0, -5300.0, 0.0, "Paint_PFSwitch")
place("SM_LB_Paint_PFDrive_v001", 13050.0, -5300.0, 0.0, "Paint_PFDrive")
# Scuff/sander decks flanking the line before the tack-off tunnel.
place("SM_LB_Paint_SanderDeck_v001", 12550.0, -7600.0, 0.0,
      "Paint_SanderDeck_N")
place("SM_LB_Paint_SanderDeck_v001", 12550.0, -9400.0, 180.0,
      "Paint_SanderDeck_S")

# ---- robots: roller-hem pair at the hemmers, sealer pair at the decks ----
ROBOT_CLASS = unreal.load_class(None,
    "/Script/LineBossCarFactory.LBBodyShopRobotActor")
if not ROBOT_CLASS:
    raise RuntimeError("LBBodyShopRobotActor class not found")
ROLE = unreal.LBBodyShopRobotRole.PANEL_HANDLING
ROBOTS = [
    (-8050.0, -5750.0, -90.0, "Weld_HemRobot_A", "WeldHem",
     unreal.LBBodyShopToolType.ROLLER_HEM),
    (-6050.0, -5750.0, -90.0, "Weld_HemRobot_B", "WeldHem",
     unreal.LBBodyShopToolType.ROLLER_HEM),
    (13300.0, -9100.0, 90.0, "Paint_SealerRobot_S", "PaintSealer",
     unreal.LBBodyShopToolType.SEALER_APPLICATOR),
    (13300.0, -7900.0, -90.0, "Paint_SealerRobot_N", "PaintSealer",
     unreal.LBBodyShopToolType.SEALER_APPLICATOR),
]
for x, y, yaw, label, cell, tool in ROBOTS:
    actor = ACTOR_SUB.spawn_actor_from_class(
        ROBOT_CLASS, unreal.Vector(x, y, 0.0), unreal.Rotator(0.0, yaw, 0.0))
    if actor is None:
        REPORT["robots"].append({"label": label, "ok": False})
        continue
    actor.tags = [unreal.Name(TAG), unreal.Name("LB.Environment.VisualOnly"),
                  unreal.Name("LB.NotProcessWIP")]
    actor.set_actor_label(label)
    slot = unreal.LBBodyShopRobotSlotDefinition()
    slot.set_editor_property("slot_id", unreal.Name(label + "_Slot"))
    slot.set_editor_property("allowed_roles", [ROLE])
    slot.set_editor_property("allowed_tools", [tool])
    assign = unreal.LBBodyShopRobotAssignment()
    assign.set_editor_property("slot_id", unreal.Name(label + "_Slot"))
    assign.set_editor_property("role", ROLE)
    assign.set_editor_property("tool", tool)
    assign.set_editor_property("enabled", True)
    assign.set_editor_property("condition01", 1.0)
    result = actor.configure_for_authored_slot(unreal.Name(cell), slot,
                                               assign)
    reason = ""
    if isinstance(result, tuple) and len(result) >= 2:
        reason = str(result[1])
    actor.set_authored_pose(unreal.LBBodyShopRobotPose.PROCESS, True)
    complete = bool(actor.has_complete_art_presentation())
    REPORT["robots"].append({"label": label, "ok": complete,
                             "reason": reason})

LEVEL_SUB.save_current_level()
REPORT["total"] = sum(REPORT["placed"].values()) + len(REPORT["robots"])
with io.open(OUT, "w", encoding="utf-8") as h:
    h.write(json.dumps(REPORT, indent=1, sort_keys=True))
unreal.log("LINE_BOSS_BATCH17 {}".format(json.dumps(REPORT, sort_keys=True)))
