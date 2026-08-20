"""Rebuild final assembly as four process lines (press standard).

Assembly held 1,099 actors but exactly one machine; its 32-piece
authored kit sat unplaced. Four existing rows become a serpentine final
assembly flow:

  y= 3609  TRIM:     door-off, cockpit install, HVAC, nutrunner cells
  y= 7391  MARRIAGE: body lowerator, marriage gantry + powertrain
                     marriage, HV battery lifts, fluid/urethane
  y= 9609  FINAL 1:  seats, glazing (native robots), door refit, wheels
  y=13391  FINAL 2:  fluids, headlamp aim, alignment, dyno, water test,
                     EOL inspection arch at the exit

Skillet carriers chain along every line; overhead track above trim and
marriage; store bays along the north wall; andon boards per line; the
SignalKit dresses all four lines. Sizes from lb_kit_bounds.json.
Idempotent via LB.AsmLine. Run with -ExecutePythonScript.
"""
import json

import unreal

TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
TAG = "LB.AsmLine"
OUT = "C:/Temp/lb_assembly_lines.json"

BOUNDS = json.load(open("C:/Temp/lb_kit_bounds.json"))["bounds"]

def mesh_of(name):
    entry = BOUNDS.get(name)
    if entry is None:
        raise RuntimeError("no bounds entry for {}".format(name))
    mesh = unreal.load_asset(entry["package"])
    if mesh is None:
        raise RuntimeError("could not load {}".format(entry["package"]))
    return mesh

ASM = ["AndonBoard", "BodyLowerator", "ChassisHanger", "ClosureFitGauge",
       "CockpitInstallAssist", "CockpitModule", "DoorCarrier",
       "EOLInspectionArch", "ErgonomicLiftPlatform", "FlashGantry",
       "FluidFillMachine", "GlassAFrameRack", "HVACModule",
       "HVBatteryInstallLift", "HeadlampAimRig", "HeavyMarriageGantry",
       "NutrunnerReactionRail", "OverheadTrackSegment",
       "PowertrainMarriage_v003", "RollsDynoBrakeTestBed",
       "SeatInstallManipulator", "SequencedPartsCart", "SkilletCarrier",
       "StoreBay", "UrethanePumpUnit", "WaterLeakTestBooth",
       "WheelAlignmentBed", "WheelCarousel", "WheelTireRack"]
NAMES = {}
for short in ASM:
    name = "SM_LB_Assembly_{}_v001".format(short) \
        if not short.endswith("_v003") else "SM_LB_Assembly_" + short
    NAMES[short] = name
ROBOT_PARTS = ["SM_LB_BodyShopRobotNative_{}_v001".format(p)
               for p in ("Base", "J1", "J2", "J3", "J4", "J5", "J6")]
SIGNAL = {
    "pillar": "SM_LB_Site_StatusPillar_v001",
    "lineboard": "SM_LB_Sign_LineBoard_v001",
    "tray": "SM_LB_Detail_CableTray_2000_v001",
    "festoon": "SM_LB_Detail_HoseFestoon_v001",
    "kanban": "SM_LB_Detail_KanbanBoard_v001",
    "marker": "SM_LB_Detail_FloorMarkerSet_v001",
}

LEVEL_SUB = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTOR_SUB = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not LEVEL_SUB.load_level(TARGET):
    raise RuntimeError("could not load target map")
world = unreal.EditorLevelLibrary.get_editor_world()
if world is None or TARGET.rsplit("/", 1)[-1] != world.get_name():
    raise RuntimeError("wrong world; use -ExecutePythonScript")

MESHES = {}
for short, name in NAMES.items():
    MESHES[short] = mesh_of(name)
for part in ROBOT_PARTS:
    MESHES[part] = mesh_of(part)
for key, name in SIGNAL.items():
    asset = unreal.load_asset("/Game/LineBoss/SignalKit_v001/" + name)
    if asset is None:
        raise RuntimeError("missing signal mesh " + name)
    MESHES[key] = asset

REPORT = {"cleared": 0, "placed": 0}
for actor in list(ACTOR_SUB.get_all_level_actors()):
    tags = [str(t) for t in actor.tags]
    kill = TAG in tags
    if not kill and actor.get_actor_label().startswith("Assembly_"):
        for component in actor.get_components_by_class(
                unreal.StaticMeshComponent):
            mesh = component.get_editor_property("static_mesh")
            if mesh and "PowertrainMarriage" in mesh.get_name():
                kill = True
    if kill:
        ACTOR_SUB.destroy_actor(actor)
        REPORT["cleared"] += 1

def spawn(key, x, y, yaw, z=0.0):
    actor = ACTOR_SUB.spawn_actor_from_object(
        MESHES[key], unreal.Vector(x, y, z), unreal.Rotator(0.0, 0.0, yaw))
    if actor is None:
        return
    REPORT["placed"] += 1
    actor.set_actor_label("AsmLine_{:04d}".format(REPORT["placed"]))
    for tag in (TAG, "LB.Environment.VisualOnly", "LB.NotProcessWIP"):
        actor.tags.append(tag)

def robot(x, y, yaw):
    for part in ROBOT_PARTS:
        spawn(part, x, y, yaw)

X_WEST, X_EAST = 4400.0, 21600.0
PITCH = 640.0
TRIM, MARRIAGE, FINAL1, FINAL2 = 3609.0, 7391.0, 9609.0, 13391.0

def cells():
    total = int((X_EAST - X_WEST - 1200.0) / PITCH)
    return [X_WEST + 900.0 + slot * PITCH for slot in range(total)]

# Skillet chains on every line; overhead track over trim and marriage.
for line_y in (TRIM, MARRIAGE, FINAL1, FINAL2):
    x = X_WEST
    while x <= X_EAST:
        spawn("SkilletCarrier", x, line_y, 0.0)
        x += 320.0
for line_y in (TRIM, MARRIAGE):
    x = X_WEST
    while x <= X_EAST:
        spawn("OverheadTrackSegment", x, line_y, 0.0, 520.0)
        x += 300.0

# TRIM line.
for slot, x in enumerate(cells()):
    phase = slot % 6
    if slot == 0:
        spawn("DoorCarrier", x, TRIM + 320.0, 0.0)
    elif phase == 0:
        spawn("CockpitInstallAssist", x, TRIM + 300.0, 180.0)
        spawn("CockpitModule", x + 240.0, TRIM + 340.0, 0.0)
    elif phase == 1:
        spawn("NutrunnerReactionRail", x, TRIM - 300.0, 0.0)
    elif phase == 2:
        spawn("HVACModule", x, TRIM + 320.0, 0.0)
        spawn("SequencedPartsCart", x + 220.0, TRIM + 320.0, 90.0)
    elif phase == 3:
        spawn("ErgonomicLiftPlatform", x, TRIM - 300.0, 180.0)
    elif phase == 4:
        spawn("SequencedPartsCart", x, TRIM + 300.0, 0.0)
        spawn("SequencedPartsCart", x + 200.0, TRIM + 300.0, 0.0)
    else:
        spawn("DoorCarrier", x, TRIM - 320.0, 180.0)
    if slot % 3 == 1:
        spawn("kanban", x, TRIM + 620.0, 180.0)

# MARRIAGE line.
marriage_cells = cells()
for slot, x in enumerate(marriage_cells):
    phase = slot % 6
    if slot == 0:
        spawn("BodyLowerator", x, MARRIAGE, 0.0)
    elif slot == 2:
        spawn("HeavyMarriageGantry", x, MARRIAGE, 0.0)
    elif slot == 3:
        spawn("PowertrainMarriage_v003", x, MARRIAGE, 0.0)
    elif phase == 4:
        spawn("HVBatteryInstallLift", x, MARRIAGE - 300.0, 0.0)
        robot(x + 260.0, MARRIAGE + 320.0, -90.0)
    elif phase == 5:
        spawn("FluidFillMachine", x, MARRIAGE + 320.0, 180.0)
        spawn("UrethanePumpUnit", x + 240.0, MARRIAGE + 340.0, 0.0)
    elif phase == 1:
        spawn("ChassisHanger", x, MARRIAGE - 320.0, 0.0)
    else:
        spawn("ShieldCart" if "ShieldCart" in MESHES else
              "SequencedPartsCart", x, MARRIAGE + 320.0, 90.0)

# FINAL 1: seats, glazing, doors back on, wheels.
final1_cells = cells()
for slot, x in enumerate(final1_cells):
    phase = slot % 6
    if phase == 0:
        spawn("SeatInstallManipulator", x, FINAL1 + 300.0, 180.0)
    elif phase == 1:
        spawn("GlassAFrameRack", x, FINAL1 + 340.0, 0.0)
        robot(x + 220.0, FINAL1 - 300.0, 90.0)
    elif phase == 2:
        spawn("ClosureFitGauge", x, FINAL1 + 300.0, 180.0)
        spawn("DoorCarrier", x + 220.0, FINAL1 + 320.0, 0.0)
    elif phase == 3:
        spawn("WheelCarousel", x, FINAL1 - 320.0, 0.0)
    elif phase == 4:
        spawn("WheelTireRack", x, FINAL1 + 320.0, 90.0)
        spawn("WheelTireRack", x + 200.0, FINAL1 + 320.0, 90.0)
    else:
        spawn("ErgonomicLiftPlatform", x, FINAL1 - 300.0, 0.0)
    if slot % 4 == 2:
        spawn("kanban", x, FINAL1 + 620.0, 180.0)

# FINAL 2: fluids, aim, alignment, dyno, leak test, EOL arch.
final2_cells = cells()
last = len(final2_cells) - 1
for slot, x in enumerate(final2_cells):
    phase = slot % 5
    if slot == last:
        spawn("EOLInspectionArch", x, FINAL2, 0.0)
    elif slot == last - 1:
        spawn("FlashGantry", x, FINAL2, 0.0)
    elif slot == last - 2:
        spawn("WaterLeakTestBooth", x, FINAL2, 0.0)
    elif slot == last - 3:
        spawn("RollsDynoBrakeTestBed", x, FINAL2 + 300.0, 0.0)
    elif slot == last - 4:
        spawn("WheelAlignmentBed", x, FINAL2 + 300.0, 0.0)
    elif phase == 0:
        spawn("FluidFillMachine", x, FINAL2 + 320.0, 180.0)
    elif phase == 1:
        spawn("HeadlampAimRig", x, FINAL2 + 300.0, 180.0)
    elif phase == 2:
        spawn("SequencedPartsCart", x, FINAL2 + 300.0, 90.0)
    else:
        spawn("ErgonomicLiftPlatform", x, FINAL2 - 300.0, 0.0)

# Store bays along the north wall; andon board per line head.
x = X_WEST + 400.0
while x <= X_EAST:
    spawn("StoreBay", x, 14300.0, 180.0)
    x += 900.0
for line_y in (TRIM, MARRIAGE, FINAL1, FINAL2):
    spawn("AndonBoard", X_WEST - 500.0, line_y + 300.0, 90.0, 300.0)
    for x, side in ((X_WEST - 500.0, 1), (X_EAST + 500.0, -1)):
        spawn("pillar", x, line_y + 300.0 * side, 0.0)
    x = X_WEST + 1200.0
    while x <= X_EAST:
        spawn("lineboard", x, line_y, 0.0, 500.0)
        x += 1280.0
    x = X_WEST
    while x <= X_EAST:
        spawn("tray", x, line_y + 520.0, 0.0, 380.0)
        x += 200.0
    x = X_WEST + 900.0
    index = 0
    while x <= X_EAST:
        if index % 2 == 0:
            spawn("festoon", x, line_y - 420.0, 0.0, 300.0)
        if index % 6 == 2:
            spawn("marker", x, line_y + 900.0, 0.0, 2.0)
        x += 640.0
        index += 1

if not LEVEL_SUB.save_current_level():
    raise RuntimeError("could not save the level")

with open(OUT, "w") as handle:
    json.dump(REPORT, handle, indent=1)
unreal.log("LINE_BOSS_ASM_LINES placed={} cleared={}".format(
    REPORT["placed"], REPORT["cleared"]))
