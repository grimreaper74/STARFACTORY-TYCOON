"""Complete the paint shop's process lines (press standard).

The ED line (y=-5300: pretreat, open dip tanks under the PF track, then
the enclosed oven) already reads correctly and is untouched. This fills
the gaps around it, additively:

  y=-8500  process line: sealer decks with robots, sander decks, a full
           four-booth spray block (shells + scrubber trenches + spray
           robots), flash-offs between booths, quality light tunnel and
           polish at the exit
  y=-4600  services: extended rectifier row, pipe bridges over the track,
           chem dosing skids (sludge/UF corner stays by the dips)
  y=-10600 booth back-of-house: AHU + air extraction per booth
  y=-12000 skid receiving: conveyor run, lift transfers, buffer racks

SignalKit dresses both lines. Idempotent via LB.PaintLine. Sizes from
lb_kit_bounds.json. Run with -ExecutePythonScript.
"""
import json

import unreal

TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
TAG = "LB.PaintLine"
OUT = "C:/Temp/lb_paint_lines.json"

BOUNDS = json.load(open("C:/Temp/lb_kit_bounds.json"))["bounds"]

def mesh_of(name):
    entry = BOUNDS.get(name)
    if entry is None:
        raise RuntimeError("no bounds entry for {}".format(name))
    mesh = unreal.load_asset(entry["package"])
    if mesh is None:
        raise RuntimeError("could not load {}".format(entry["package"]))
    return mesh

PAINT = ["SM_LB_Paint_PretreatmentWashTunnel_v001",
         "SM_LB_Paint_SealerDeck_v001", "SM_LB_Paint_SealerNozzleTool_v001",
         "SM_LB_Paint_SanderDeck_v001", "SM_LB_Paint_SprayBoothShell_v001",
         "SM_LB_Paint_BoothScrubberTrench_v001",
         "SM_LB_Paint_SprayApplicatorTool_v001",
         "SM_LB_Paint_FlashOffTunnel_v001",
         "SM_LB_Paint_QualityLightTunnel_v001",
         "SM_LB_Paint_PolishDeck_v001", "SM_LB_Paint_RectifierCabinet_v001",
         "SM_LB_Paint_PipeBridge_Module_v001",
         "SM_LB_Paint_ChemDosingSkid_v001", "SM_LB_Paint_AHU_Module_v001",
         "SM_LB_Paint_AirExtractionModule_v001",
         "SM_LB_Paint_ServiceSet_v001", "SM_LB_Paint_BodySkidCarrier_v001",
         "SM_LB_Weld_SkidConveyorModule_3000_v001",
         "SM_LB_Weld_SkidLiftTransfer_v001", "SM_LB_Weld_BIWBufferRack_v001"]
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

MESHES = {name: mesh_of(name) for name in PAINT}
for part in ROBOT_PARTS:
    MESHES[part] = mesh_of(part)
for key, name in SIGNAL.items():
    asset = unreal.load_asset("/Game/LineBoss/SignalKit_v001/" + name)
    if asset is None:
        raise RuntimeError("missing signal mesh " + name)
    MESHES[key] = asset

REPORT = {"cleared": 0, "placed": 0}
for actor in list(ACTOR_SUB.get_all_level_actors()):
    if TAG in [str(t) for t in actor.tags]:
        ACTOR_SUB.destroy_actor(actor)
        REPORT["cleared"] += 1

def spawn(key, x, y, yaw, z=0.0):
    actor = ACTOR_SUB.spawn_actor_from_object(
        MESHES[key], unreal.Vector(x, y, z), unreal.Rotator(0.0, 0.0, yaw))
    if actor is None:
        return
    REPORT["placed"] += 1
    actor.set_actor_label("PaintLine_{:04d}".format(REPORT["placed"]))
    for tag in (TAG, "LB.Environment.VisualOnly", "LB.NotProcessWIP"):
        actor.tags.append(tag)

def robot(x, y, yaw):
    for part in ROBOT_PARTS:
        spawn(part, x, y, yaw)

ED_Y, PROC_Y, SVC_Y, BOH_Y, SKID_Y = -5300.0, -8500.0, -4600.0, \
    -10600.0, -12000.0

# ED line head: the pretreatment wash tunnel ahead of the spray stage.
spawn("SM_LB_Paint_PretreatmentWashTunnel_v001", -1100.0, ED_Y, 0.0)

# Services along the ED run: rectifiers every 12 m (three exist), pipe
# bridges over the track every 18 m, dosing skids by the tanks.
x = 1300.0
while x <= 11300.0:
    spawn("SM_LB_Paint_RectifierCabinet_v001", x, SVC_Y, 180.0)
    x += 1200.0
x = 1400.0
while x <= 11000.0:
    spawn("SM_LB_Paint_PipeBridge_Module_v001", x, ED_Y + 650.0, 0.0)
    x += 1800.0
spawn("SM_LB_Paint_ChemDosingSkid_v001", 4600.0, SVC_Y - 300.0, 0.0)
spawn("SM_LB_Paint_ChemDosingSkid_v001", 8600.0, SVC_Y - 300.0, 0.0)

# Process line, west half: sealer cells then sander decks.
for index in range(4):
    x = 1200.0 + index * 1500.0
    spawn("SM_LB_Paint_SealerDeck_v001", x, PROC_Y, 0.0)
    spawn("SM_LB_Paint_SealerNozzleTool_v001", x, PROC_Y + 260.0, 180.0)
    robot(x - 260.0, PROC_Y - 320.0, 90.0)
    robot(x + 260.0, PROC_Y + 320.0, -90.0)
for index in range(3):
    x = 7600.0 + index * 1300.0
    spawn("SM_LB_Paint_SanderDeck_v001", x, PROC_Y, 0.0)
    robot(x, PROC_Y + 320.0, -90.0)
spawn("SM_LB_Paint_ServiceSet_v001", 6600.0, PROC_Y + 400.0, 0.0)
spawn("SM_LB_Paint_ServiceSet_v001", 11300.0, PROC_Y - 400.0, 180.0)

# Booth block: two more shells between the existing pair, robots inside
# every shell, scrubber trench under and AHU + extraction behind each.
for x in (15400.0, 17300.0):
    spawn("SM_LB_Paint_SprayBoothShell_v001", x, PROC_Y, 0.0)
    spawn("SM_LB_Paint_BoothScrubberTrench_v001", x, PROC_Y - 1100.0, 0.0)
for x in (14500.0, 15400.0, 17300.0, 18200.0):
    robot(x - 220.0, PROC_Y + 200.0, -90.0)
    robot(x + 220.0, PROC_Y - 200.0, 90.0)
    spawn("SM_LB_Paint_AHU_Module_v001", x - 150.0, BOH_Y, 0.0)
    spawn("SM_LB_Paint_AirExtractionModule_v001", x + 260.0, BOH_Y, 0.0)
# Flash-off between booths dropped: the shells leave no true gap;
# the two existing flash-offs after the block carry that stage.

# Exit: quality light tunnel after the polish decks.
spawn("SM_LB_Paint_QualityLightTunnel_v001", 21400.0, PROC_Y, 0.0)
spawn("SM_LB_Paint_PolishDeck_v001", 20450.0, PROC_Y, 0.0)

# Skid receiving row: conveyor run with lifts and buffer racks, carriers
# staged along it.
x = 800.0
while x <= 11600.0:
    spawn("SM_LB_Weld_SkidConveyorModule_3000_v001", x, SKID_Y, 0.0)
    x += 305.0
spawn("SM_LB_Weld_SkidLiftTransfer_v001", 500.0, SKID_Y, 0.0)
spawn("SM_LB_Weld_SkidLiftTransfer_v001", 11900.0, SKID_Y, 0.0)
for index in range(4):
    spawn("SM_LB_Paint_BodySkidCarrier_v001", 1600.0 + index * 2600.0,
          SKID_Y + 420.0, 0.0)
for index in range(3):
    spawn("SM_LB_Weld_BIWBufferRack_v001", 12600.0 + index * 520.0,
          SKID_Y, 90.0)

# SignalKit dressing on both working lines.
for line_y in (PROC_Y, SKID_Y):
    for x, side in ((300.0, 1), (21800.0 if line_y == PROC_Y else 12400.0,
                                 -1)):
        spawn("pillar", x, line_y + 300.0 * side, 0.0)
    x = 1500.0
    end = 21000.0 if line_y == PROC_Y else 11600.0
    while x <= end:
        spawn("lineboard", x, line_y, 0.0, 500.0)
        x += 1280.0
    x = 500.0
    while x <= end:
        spawn("tray", x, line_y + 520.0, 0.0, 380.0)
        x += 200.0
    x = 900.0
    index = 0
    while x <= end:
        if index % 2 == 0:
            spawn("festoon", x, line_y - 420.0, 0.0, 300.0)
        if index % 4 == 1:
            spawn("kanban", x, line_y + 760.0, 180.0)
        if index % 6 == 2:
            spawn("marker", x, line_y + 900.0, 0.0, 2.0)
        x += 640.0
        index += 1

if not LEVEL_SUB.save_current_level():
    raise RuntimeError("could not save the level")

with open(OUT, "w") as handle:
    json.dump(REPORT, handle, indent=1)
unreal.log("LINE_BOSS_PAINT_LINES placed={} cleared={}".format(
    REPORT["placed"], REPORT["cleared"]))
