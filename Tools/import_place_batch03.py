"""Batch 03: import seven assembly machines, place them, and stand the robots.

Robots use the native ALBBodyShopRobotActor, which assembles its own seven-mesh
presentation and takes an authored pose - no hand-composed joint transforms.
Four go into the two paint booths, two form the glazing pair at assembly
station 7 (Task 31 scope for the placed booths).

Skillet plates skip a 350 cm window at each station centre so the frozen
carriers and my plates never interpenetrate. Idempotent via LB.Batch03.
"""
import io
import json
import os

import unreal

SRC = (r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8"
       r"/SourceAssets/Candidate")
TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
TAG = "LB.Batch03"
OUT = os.environ.get("LB_BATCH_OUT", "C:/Temp/lb_batch03.json")

MODELS = [
    ("AssemblyShop/SkilletDeckPlate_v001", "SM_LB_Conveyor_SkilletDeckPlate_v001"),
    ("AssemblyShop/OverheadTrack_v001", "SM_LB_Assembly_OverheadTrackSegment_v001"),
    ("AssemblyShop/ChassisHanger_v001", "SM_LB_Assembly_ChassisHanger_v001"),
    ("AssemblyShop/HVBatteryLift_v001", "SM_LB_Assembly_HVBatteryInstallLift_v001"),
    ("AssemblyShop/FluidFill_v001", "SM_LB_Assembly_FluidFillMachine_v001"),
    ("AssemblyShop/SeatManipulator_v001", "SM_LB_Assembly_SeatInstallManipulator_v001"),
    ("AssemblyShop/NutrunnerRail_v001", "SM_LB_Assembly_NutrunnerReactionRail_v001"),
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
    if mesh is None:
        raise RuntimeError("could not load {}".format(paths[0]))
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

PLATE = "SM_LB_Conveyor_SkilletDeckPlate_v001"
TRIM_STATIONS = [4000.0 + n * 2200.0 for n in range(8)]
FINAL_STATIONS = [28200.0 - n * 2200.0 for n in range(2, 6)]  # stations 15-18


def clear_of(x, stations, window=350.0):
    return all(abs(x - s) > window for s in stations)


# Trim line moving floor (stations 1-8, y 5500).
x = 3000.0
while x <= 19400.0:
    if clear_of(x, TRIM_STATIONS):
        place(PLATE, x, 5500.0, 0.0, "Asm_Skillet_Trim")
    x += 200.0
# Final line moving floor (stations 15-18, y 11500).
x = 16400.0
while x <= 25200.0:
    if clear_of(x, FINAL_STATIONS):
        place(PLATE, x, 11500.0, 0.0, "Asm_Skillet_Final")
    x += 200.0

# Overhead chassis line: marriage run then the underbody return leg.
for n in range(12):
    place("SM_LB_Assembly_OverheadTrackSegment_v001", 22600.0 + n * 400.0,
          5500.0, 0.0, "Asm_Track_Marriage")
for n in range(6):
    place("SM_LB_Assembly_OverheadTrackSegment_v001", 26600.0 + n * 400.0,
          11500.0, 0.0, "Asm_Track_Underbody")
for hx in (23000.0, 24200.0, 25400.0, 26600.0):
    place("SM_LB_Assembly_ChassisHanger_v001", hx, 5500.0, 0.0, "Asm_Hanger")
for hx in (27000.0, 28200.0):
    place("SM_LB_Assembly_ChassisHanger_v001", hx, 11500.0, 0.0, "Asm_Hanger")

# Decking lifts under the elevated body at marriage stations 10 and 11.
place("SM_LB_Assembly_HVBatteryInstallLift_v001", 23800.0, 5500.0, 0.0,
      "Asm_BatteryLift_S10")
place("SM_LB_Assembly_HVBatteryInstallLift_v001", 26000.0, 5500.0, 0.0,
      "Asm_BatteryLift_S11")

# Fluid farm behind the final line; seat cell beside station 15; tool rails.
for n in range(4):
    place("SM_LB_Assembly_FluidFillMachine_v001", 17800.0 + n * 600.0,
          12400.0, 180.0, "Asm_FluidFill")
place("SM_LB_Assembly_SeatInstallManipulator_v001", 23800.0, 12250.0, 0.0,
      "Asm_SeatCell_S15")
place("SM_LB_Assembly_NutrunnerReactionRail_v001", 8400.0, 4800.0, 0.0,
      "Asm_ToolRail_Trim1")
place("SM_LB_Assembly_NutrunnerReactionRail_v001", 14000.0, 4800.0, 0.0,
      "Asm_ToolRail_Trim2")
place("SM_LB_Assembly_NutrunnerReactionRail_v001", 26800.0, 10800.0, 0.0,
      "Asm_ToolRail_Underbody")

# ---- robots: native self-assembling actor, posed and saved ------------------
ROBOT_CLASS = unreal.load_class(None,
    "/Script/LineBossCarFactory.LBBodyShopRobotActor")
if ROBOT_CLASS is None:
    raise RuntimeError("LBBodyShopRobotActor class not found")

ROLE = unreal.LBBodyShopRobotRole.PANEL_HANDLING
TOOL = unreal.LBBodyShopToolType.VACUUM_EIGHT_CUP
ROBOTS = [
    (14200.0, -8650.0, 0.0, "Paint_Booth_E1_RobotA", "PaintE1"),
    (14800.0, -8350.0, 180.0, "Paint_Booth_E1_RobotB", "PaintE1"),
    (17900.0, -8650.0, 0.0, "Paint_Booth_E2_RobotA", "PaintE2"),
    (18500.0, -8350.0, 180.0, "Paint_Booth_E2_RobotB", "PaintE2"),
    (17200.0, 5780.0, -90.0, "Asm_GlazingRobot_L", "AsmGlazing"),
    (17200.0, 5220.0, 90.0, "Asm_GlazingRobot_R", "AsmGlazing"),
]
for x, y, yaw, label, cell in ROBOTS:
    actor = ACTOR_SUB.spawn_actor_from_class(
        ROBOT_CLASS, unreal.Vector(x, y, 0.0), unreal.Rotator(0.0, yaw, 0.0))
    if actor is None:
        REPORT["robots"].append({"label": label, "ok": False})
        continue
    actor.tags = [unreal.Name(TAG), unreal.Name("LB.Environment.VisualOnly"),
                  unreal.Name("LB.NotProcessWIP")]
    actor.set_actor_label(label)
    # The art presentation only loads through ConfigureForAuthoredSlot.
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
    result = actor.configure_for_authored_slot(unreal.Name(cell), slot,
                                               assign)
    # Binding return shape varies; the art flag is the authoritative gate.
    reason = ""
    if isinstance(result, tuple) and len(result) >= 2:
        reason = str(result[1])
    actor.set_authored_pose(unreal.LBBodyShopRobotPose.PROCESS, True)
    complete = bool(actor.has_complete_art_presentation())
    REPORT["robots"].append({"label": label, "ok": complete,
                             "raw": repr(result), "reason": reason})

LEVEL_SUB.save_current_level()
REPORT["total"] = sum(REPORT["placed"].values()) + len(REPORT["robots"])
with io.open(OUT, "w", encoding="utf-8") as h:
    h.write(json.dumps(REPORT, indent=1, sort_keys=True))
unreal.log("LINE_BOSS_BATCH03 {}".format(json.dumps(REPORT, sort_keys=True)))
