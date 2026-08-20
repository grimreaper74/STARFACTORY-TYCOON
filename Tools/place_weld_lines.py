"""Rebuild body weld as three coherent process lines (press standard).

Owner (2026-08-20): the shops other than press are "just objects randamly
placed". This lays the authored 26-piece weld kit out in process order
along the three existing machine rows:

  north  (y=-5192)  underbody build: fixtures, geo pins, pedestal welders
  middle (y=-9099)  framing + respot: framing gates, respot cells, vision
  south  (y=-13067) closures + finish: hemming, turntables, benches, CMM,
                    rework, BIW buffer at the east exit

Each line gets a continuous skid-conveyor chain, native robots posed at
the cells (all seven joint meshes share one transform - pivots baked),
support kit behind the cells, and inbound stillages only at the west
line heads. Replaces the earlier scatter pass (LB.WeldDensity) and the
14 stray conveyor modules. Idempotent via LB.WeldLine. Sizes from
C:/Temp/lb_kit_bounds.json. Run with -ExecutePythonScript.
"""
import json

import unreal

TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
TAG = "LB.WeldLine"
OUT = "C:/Temp/lb_weld_lines.json"

BOUNDS = json.load(open("C:/Temp/lb_kit_bounds.json"))["bounds"]

def mesh_of(name):
    entry = BOUNDS.get(name)
    if entry is None:
        raise RuntimeError("no bounds entry for {}".format(name))
    mesh = unreal.load_asset(entry["package"])
    if mesh is None:
        raise RuntimeError("could not load {}".format(entry["package"]))
    return mesh

NAMES = [
    "SM_LB_Weld_SkidConveyorModule_3000_v001",
    "SM_LB_Weld_SkidLiftTransfer_v001",
    "SM_LB_BodyShop_UnderbodyFixture_v001",
    "SM_LB_Weld_GeoPinUnit_v001", "SM_LB_Weld_ClampUnit_v001",
    "SM_LB_Weld_PedestalWelder_v001", "SM_LB_Weld_StudFeeder_v001",
    "SM_LB_Weld_FramingGate_v001", "SM_LB_Weld_RespotFixture_v001",
    "SM_LB_Weld_RespotGunStand_v001", "SM_LB_Weld_TipDresser_v001",
    "SM_LB_Weld_IndexTurntable_v001", "SM_LB_BodyShop_VisionGate_v001",
    "SM_LB_Weld_HemmingPress_v001", "SM_LB_BodyShop_ClosureTurntable_v001",
    "SM_LB_Weld_ClosureDoorFixture_v001",
    "SM_LB_Weld_OverheadDropLift_v001",
    "SM_LB_Weld_MetalFinishBench_v001", "SM_LB_Weld_CMMBed_v001",
    "SM_LB_Weld_ReworkBoothFrame_v001", "SM_LB_Weld_BIWBufferRack_v001",
    "SM_LB_Weld_MarshallingRack_v001", "SM_LB_Weld_RoofMagazine_v001",
    "SM_LB_Weld_WaterChillerSkid_v001",
    "SM_LB_BodyShopSupport_ElectricalCabinet_v002",
    "SM_LB_BodyShopSupport_HMIPedestal_v002",
    "SM_LB_BodyShopSupport_ExtractionPedestal_v002",
    "SM_LB_BodyShopSupport_PanelStillage_Full_v002",
    "SM_LB_BodyShopSupport_PanelStillage_Empty_v002",
    "SM_LB_BodyShopSupport_EmptyReturnCart_v002",
    "SM_LB_BodyShopSupport_SmallPartsCrate_Open_v002",
    "SM_LB_BodyShopRobotNative_Base_v001",
    "SM_LB_BodyShopRobotNative_J1_v001",
    "SM_LB_BodyShopRobotNative_J2_v001",
    "SM_LB_BodyShopRobotNative_J3_v001",
    "SM_LB_BodyShopRobotNative_J4_v001",
    "SM_LB_BodyShopRobotNative_J5_v001",
    "SM_LB_BodyShopRobotNative_J6_v001",
]
ROBOT_PARTS = [n for n in NAMES if "RobotNative" in n]

LEVEL_SUB = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTOR_SUB = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not LEVEL_SUB.load_level(TARGET):
    raise RuntimeError("could not load target map")
world = unreal.EditorLevelLibrary.get_editor_world()
if world is None or TARGET.rsplit("/", 1)[-1] != world.get_name():
    raise RuntimeError("wrong world; use -ExecutePythonScript")

MESHES = {name: mesh_of(name) for name in NAMES}
REPORT = {"cleared": 0, "placed": 0}

# Clear: this pass's own tag, the rejected scatter pass, and the stray
# conveyor modules from the old dressing.
for actor in list(ACTOR_SUB.get_all_level_actors()):
    tags = [str(t) for t in actor.tags]
    kill = TAG in tags or "LB.WeldDensity" in tags
    if not kill and actor.get_actor_label().startswith("Weld_"):
        for component in actor.get_components_by_class(
                unreal.StaticMeshComponent):
            mesh = component.get_editor_property("static_mesh")
            if mesh and mesh.get_name() in (
                    "SM_LB_Weld_SkidConveyorModule_3000_v001",
                    "SM_LB_PanelStillage_Runtime_v001"):
                kill = True
    if kill:
        ACTOR_SUB.destroy_actor(actor)
        REPORT["cleared"] += 1

def spawn(name, x, y, yaw, z=0.0):
    actor = ACTOR_SUB.spawn_actor_from_object(
        MESHES[name], unreal.Vector(x, y, z),
        unreal.Rotator(0.0, 0.0, yaw))
    if actor is None:
        return None
    REPORT["placed"] += 1
    actor.set_actor_label("WeldLine_{:04d}".format(REPORT["placed"]))
    for tag in (TAG, "LB.Environment.VisualOnly", "LB.NotProcessWIP"):
        actor.tags.append(tag)
    return actor

def robot(x, y, yaw):
    for part in ROBOT_PARTS:
        spawn(part, x, y, yaw)

X_WEST, X_EAST = -19500.0, -3400.0
# Real body lines run ~6 m station pitch; the first pass used 18 m and
# read as scattered objects however much was placed.
PITCH = 640.0
NORTH, MIDDLE, SOUTH = -5192.0, -9099.0, -13067.0

# Conveyor chains: continuous skid modules along each line, a lift
# transfer at both ends of each chain.
for line_y in (NORTH, MIDDLE, SOUTH):
    x = X_WEST
    while x <= X_EAST:
        spawn("SM_LB_Weld_SkidConveyorModule_3000_v001", x, line_y, 0.0)
        x += 305.0
    spawn("SM_LB_Weld_SkidLiftTransfer_v001", X_WEST - 300.0, line_y, 0.0)
    spawn("SM_LB_Weld_SkidLiftTransfer_v001", X_EAST + 300.0, line_y, 0.0)

def cell_positions(count=None):
    total = int((X_EAST - X_WEST - 1200.0) / PITCH)
    if count is not None:
        total = count
    return [X_WEST + 900.0 + slot * PITCH for slot in range(total)]

# North line - underbody build.
for slot, x in enumerate(cell_positions()):
    if slot % 3 == 0:
        spawn("SM_LB_BodyShop_UnderbodyFixture_v001", x, NORTH + 420.0, 0.0)
        robot(x - 320.0, NORTH - 320.0, 90.0)
        robot(x + 320.0, NORTH - 320.0, 90.0)
    elif slot % 3 == 1:
        spawn("SM_LB_Weld_PedestalWelder_v001", x, NORTH + 300.0, 180.0)
        spawn("SM_LB_Weld_StudFeeder_v001", x + 260.0, NORTH + 320.0, 0.0)
        robot(x, NORTH - 300.0, 90.0)
    else:
        robot(x - 180.0, NORTH + 300.0, -90.0)
        robot(x + 180.0, NORTH - 300.0, 90.0)
        spawn("SM_LB_Weld_TipDresser_v001", x + 420.0, NORTH + 240.0, 0.0)
    if slot % 2 == 0:
        spawn("SM_LB_BodyShopSupport_HMIPedestal_v002", x - 300.0,
              NORTH + 640.0, 180.0)
    else:
        spawn("SM_LB_BodyShopSupport_ElectricalCabinet_v002", x + 300.0,
              NORTH + 540.0, 180.0)

# Middle line - framing gates then respot cells then vision gate.
mid_cells = cell_positions()
last = len(mid_cells) - 1
for slot, x in enumerate(mid_cells):
    if slot < 3:
        spawn("SM_LB_Weld_FramingGate_v001", x, MIDDLE, 0.0)
        robot(x - 380.0, MIDDLE + 340.0, -90.0)
        robot(x - 380.0, MIDDLE - 340.0, 90.0)
    elif slot == last:
        spawn("SM_LB_BodyShop_VisionGate_v001", x, MIDDLE, 0.0)
    elif slot == last - 1:
        spawn("SM_LB_Weld_IndexTurntable_v001", x, MIDDLE, 0.0)
        robot(x - 300.0, MIDDLE + 320.0, -90.0)
    else:
        spawn("SM_LB_Weld_RespotFixture_v001", x, MIDDLE + 240.0, 0.0)
        robot(x - 180.0, MIDDLE - 300.0, 90.0)
        robot(x + 180.0, MIDDLE - 300.0, 90.0)
        if slot % 2 == 0:
            spawn("SM_LB_Weld_RespotGunStand_v001", x - 260.0,
                  MIDDLE + 380.0, 180.0)
        else:
            spawn("SM_LB_Weld_TipDresser_v001", x + 260.0, MIDDLE + 380.0,
                  180.0)
    if slot % 2 == 0:
        spawn("SM_LB_BodyShopSupport_ElectricalCabinet_v002", x,
              MIDDLE + 700.0, 180.0)

# South line - closures and finish, west to east.
south_cells = cell_positions()
last = len(south_cells) - 1
for slot, x in enumerate(south_cells):
    phase = slot % 6
    if slot < 3:
        spawn("SM_LB_Weld_HemmingPress_v001", x, SOUTH + 300.0, 180.0)
        robot(x, SOUTH - 300.0, 90.0)
    elif slot == last:
        spawn("SM_LB_Weld_ReworkBoothFrame_v001", x, SOUTH + 320.0, 0.0)
    elif slot == last - 1:
        spawn("SM_LB_Weld_CMMBed_v001", x, SOUTH + 300.0, 0.0)
    elif phase in (0, 3):
        spawn("SM_LB_BodyShop_ClosureTurntable_v001", x, SOUTH + 300.0,
              0.0)
        robot(x + 260.0, SOUTH - 300.0, 90.0)
    elif phase in (1, 4):
        spawn("SM_LB_Weld_ClosureDoorFixture_v001", x - 150.0,
              SOUTH + 280.0, 0.0)
        spawn("SM_LB_Weld_ClosureDoorFixture_v001", x + 150.0,
              SOUTH + 280.0, 0.0)
        robot(x, SOUTH - 300.0, 90.0)
    elif phase == 2:
        spawn("SM_LB_Weld_OverheadDropLift_v001", x, SOUTH, 0.0)
    else:
        spawn("SM_LB_Weld_MetalFinishBench_v001", x, SOUTH + 280.0, 180.0)
        spawn("SM_LB_BodyShopSupport_ExtractionPedestal_v002", x + 240.0,
              SOUTH + 300.0, 0.0)
    if slot % 2 == 1:
        spawn("SM_LB_BodyShopSupport_HMIPedestal_v002", x - 300.0,
              SOUTH + 640.0, 180.0)

# Infill rows midway between the wide-spaced main lines: door/closure
# sub-assembly cells alternating with marshalling racking, so the aisles
# read as working logistics lanes rather than empty floor.
for infill_y in (-7145.0, -11083.0):
    for slot, x in enumerate(cell_positions()):
        if slot % 2 == 0:
            for rack in range(4):
                name = ("SM_LB_BodyShopSupport_PanelStillage_Full_v002"
                        if (slot + rack) % 2 == 0 else
                        "SM_LB_BodyShopSupport_PanelStillage_Empty_v002")
                spawn(name, x - 300.0 + rack * 200.0, infill_y, 90.0)
            spawn("SM_LB_BodyShopSupport_EmptyReturnCart_v002", x + 560.0,
                  infill_y, 0.0)
        else:
            spawn("SM_LB_Weld_ClosureDoorFixture_v001", x - 160.0,
                  infill_y, 0.0)
            spawn("SM_LB_Weld_ClosureDoorFixture_v001", x + 160.0,
                  infill_y, 180.0)
            robot(x + 460.0, infill_y, 180.0)
            spawn("SM_LB_BodyShopSupport_SmallPartsCrate_Open_v002",
                  x - 460.0, infill_y + 280.0, 0.0)

# East exit buffer and services; inbound logistics only at the west heads.
for index in range(3):
    spawn("SM_LB_Weld_BIWBufferRack_v001", X_EAST - 200.0 + index * 520.0,
          SOUTH - 720.0, 90.0)
spawn("SM_LB_Weld_WaterChillerSkid_v001", X_WEST + 600.0, SOUTH - 800.0,
      0.0)
spawn("SM_LB_Weld_WaterChillerSkid_v001", X_WEST + 980.0, SOUTH - 800.0,
      0.0)
for line_y in (NORTH, MIDDLE, SOUTH):
    spawn("SM_LB_Weld_MarshallingRack_v001", X_WEST - 700.0, line_y + 560.0,
          90.0)
    spawn("SM_LB_Weld_RoofMagazine_v001", X_WEST - 700.0, line_y - 380.0,
          90.0)
    for pair in range(3):
        name = ("SM_LB_BodyShopSupport_PanelStillage_Full_v002"
                if pair % 2 == 0 else
                "SM_LB_BodyShopSupport_PanelStillage_Empty_v002")
        spawn(name, X_WEST - 1150.0, line_y - 300.0 + pair * 300.0, 90.0)

if not LEVEL_SUB.save_current_level():
    raise RuntimeError("could not save the level")

with open(OUT, "w") as handle:
    json.dump(REPORT, handle, indent=1)
unreal.log("LINE_BOSS_WELD_LINES placed={} cleared={}".format(
    REPORT["placed"], REPORT["cleared"]))
