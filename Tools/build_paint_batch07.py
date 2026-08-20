"""Journey batch 7 - paint decks, PF hardware and the body skid.

Lights-out plant: the decks are robot service platforms (pedestal
sockets, extraction, tool gantries) - no walkway furniture. PF drive
and switch are the overhead-chain machines; turntable and skid carry
the body. Original names into DetailUplift for the standard swap.
"""
import math
import sys

sys.path.append(r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
import bpy  # noqa: E402
import lb_model_kit as kit  # noqa: E402


def out(name):
    return "DetailUplift_v001/" + name


def deck_base(length, depth, height, name="DeckFrame"):
    kit.box(name, (length, depth, 0.12), (0.0, 0.0, height), kit.STEEL)
    kit.box("KickPlate", (length, 0.05, 0.12), (0.0, depth / 2.0 - 0.03,
            height + 0.10), kit.GREEN)
    kit.box("KickPlate", (length, 0.05, 0.12), (0.0, -depth / 2.0 + 0.03,
            height + 0.10), kit.GREEN)
    legs = max(2, int(length // 1.6))
    for i in range(legs):
        lx = -length / 2.0 + 0.3 + i * (length - 0.6) / (legs - 1)
        for sy in (-depth / 2.0 + 0.15, depth / 2.0 - 0.15):
            kit.box("Leg", (0.10, 0.10, height), (lx, sy, height / 2.0),
                    kit.GREEN)
    kit.box("CableTray", (length - 0.4, 0.16, 0.10),
            (0.0, -depth / 2.0 + 0.10, height - 0.18), kit.CHARCOAL)


# ---- sealer deck: robot pedestals + sealant drum station ----
NAME = "SM_LB_Paint_SealerDeck_v001"
kit.reset(); kit.glass_material()
deck_base(5.3, 2.0, 0.55)
for px in (-1.6, 0.4):
    kit.box("PedestalPlate", (0.8, 0.8, 0.08), (px, 0.0, 0.65),
            kit.CHARCOAL)
    for bx in (-0.3, 0.3):
        for by in (-0.3, 0.3):
            kit.cyl("Bolt", 0.03, 0.06, (px + bx, by, 0.72), kit.STEEL,
                    verts=8)
for i, dx in enumerate((2.03, 2.5)):
    kit.cyl("SealantDrum", 0.22, 0.9, (dx, -0.4, 1.06), kit.GREEN
            if i == 0 else kit.CHARCOAL, verts=16)
    kit.cyl("DrumPump", 0.05, 0.5, (dx, -0.4, 1.75), kit.STEEL,
            verts=8)
kit.box("PumpPanel", (0.5, 0.35, 0.7), (2.25, 0.55, 0.96), kit.GREEN)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=7.0,
                                         height=2.2)

# ---- sander deck: pedestals + dust extraction spine ----
NAME = "SM_LB_Paint_SanderDeck_v001"
kit.reset(); kit.glass_material()
deck_base(5.95, 1.6, 0.55)
for px in (-1.8, 1.8):
    kit.box("PedestalPlate", (0.75, 0.75, 0.08), (px, 0.1, 0.65),
            kit.CHARCOAL)
kit.box("ExtractDuct", (5.9, 0.30, 0.30), (0.0, -0.62, 1.85),
        kit.STEEL)
for hx in (-1.8, 0.0, 1.8):
    kit.cyl("DropHose", 0.07, 1.1, (hx, -0.62, 1.25), kit.CHARCOAL,
            verts=10)
    kit.box("DuctPost", (0.09, 0.09, 1.7), (hx - 0.9 if hx < 0
            else hx + 0.9, -0.62, 0.85), kit.GREEN)
kit.cyl("CycloneCan", 0.30, 0.8, (2.75, -0.55, 1.5), kit.STEEL,
        verts=16)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=7.5,
                                         height=2.6)

# ---- polish deck: pedestals + overhead tool gantry ----
NAME = "SM_LB_Paint_PolishDeck_v001"
kit.reset(); kit.glass_material()
deck_base(5.95, 1.6, 0.55)
for px in (-1.7, 1.7):
    kit.box("PedestalPlate", (0.75, 0.75, 0.08), (px, 0.15, 0.65),
            kit.CHARCOAL)
for gx in (-2.7, 2.7):
    kit.box("GantryPost", (0.12, 0.12, 2.9), (gx, -0.5, 1.45),
            kit.GREEN)
kit.box("GantryRail", (5.9, 0.14, 0.16), (0.0, -0.5, 2.95), kit.GREEN)
for tx in (-1.5, 0.0, 1.5):
    kit.cyl("ToolDrop", 0.04, 0.9, (tx, -0.5, 2.45), kit.CHARCOAL,
            verts=8)
    kit.cyl("PolisherHead", 0.12, 0.14, (tx, -0.5, 1.95), kit.STEEL,
            verts=12)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=7.5,
                                         height=3.2)

# ---- pretreat spray stage: portal over drain basin, ring header ----
NAME = "SM_LB_Paint_PretreatSprayStage_v001"
kit.reset(); kit.glass_material()
kit.box("DrainBasin", (4.2, 4.4, 0.22), (0.0, 0.0, 0.11), kit.CHARCOAL)
kit.box("GratingLane", (4.2, 2.6, 0.06), (0.0, 0.0, 0.25), kit.STEEL)
for sx in (-1.95, 1.95):
    for sy in (-2.05, 2.05):
        kit.column("Post", (sx, sy, 0.0), 3.1, kit.STEEL, width=0.14)
for sy in (-2.05, 2.05):
    kit.box("HeadBeam", (4.1, 0.16, 0.18), (0.0, sy, 3.20), kit.STEEL)
kit.box("CrossBeam", (0.16, 4.2, 0.18), (-1.95, 0.0, 3.20), kit.STEEL)
kit.box("CrossBeam", (0.16, 4.2, 0.18), (1.95, 0.0, 3.20), kit.STEEL)
for ry in (-1.5, 1.5):
    kit.cyl("RingHeader", 0.08, 4.0, (0.0, ry, 2.9), kit.STEEL,
            axis="X", verts=10)
    for nx in (-1.4, -0.5, 0.5, 1.4):
        kit.cyl("Nozzle", 0.03, 0.15, (nx, ry, 2.78), kit.CHARCOAL,
                verts=6)
kit.cyl("FeedRiser", 0.10, 3.0, (1.95, 2.05, 1.5), kit.STEEL, verts=10)
kit.cyl("FeedValve", 0.12, 0.10, (1.95, 2.05, 1.0), kit.RED, verts=10,
        axis="Y")
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=8.5,
                                         height=3.6)

# ---- PF drive: chain drive tower ----
NAME = "SM_LB_Paint_PFDrive_v001"
kit.reset(); kit.glass_material()
for sy in (-1.85, 1.85):
    kit.column("Leg", (0.0, sy, 0.0), 5.8, kit.GREEN, width=0.20)
kit.box("CrossBeam", (0.20, 3.9, 0.24), (0.0, 0.0, 5.80), kit.GREEN)
kit.box("DriveHouse", (1.9, 1.3, 1.0), (0.0, 0.0, 5.25), kit.STEEL)
kit.cyl("MotorCan", 0.30, 0.8, (0.0, 0.95, 5.25), kit.CHARCOAL,
        axis="Y", verts=16)
kit.cyl("SprocketHub", 0.45, 0.25, (0.0, 0.0, 4.62), kit.CHARCOAL,
        verts=20)
kit.box("ChainGuard", (0.35, 0.16, 4.2), (0.55, 0.0, 2.6),
        kit.CHARCOAL)
kit.box("TakeUpFrame", (0.6, 0.45, 0.5), (0.55, 0.0, 0.30),
        kit.GREEN)
kit.box("ControlCab", (0.9, 0.5, 1.4), (0.0, -1.55, 0.72), kit.GREEN)
kit.box("CabDoorSeam", (0.04, 0.44, 1.28), (0.46, -1.55, 0.72),
        kit.CHARCOAL, chamfer=False)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=9.0,
                                         height=5.2)

# ---- PF switch: diverging track portal with frog actuator ----
NAME = "SM_LB_Paint_PFSwitch_v001"
kit.reset(); kit.glass_material()
for sy in (-1.85, 1.85):
    kit.column("Leg", (-1.5, sy, 0.0), 5.5, kit.GREEN, width=0.18)
    kit.column("Leg", (1.5, sy, 0.0), 5.5, kit.GREEN, width=0.18)
for lx in (-1.5, 1.5):
    kit.box("CrossBeam", (0.18, 3.9, 0.22), (lx, 0.0, 5.50), kit.GREEN)
kit.box("MainRail", (4.25, 0.16, 0.28), (0.0, 0.0, 5.30), kit.STEEL)
kit.box("BranchRail", (2.4, 0.16, 0.28), (0.95, 0.75, 5.30), kit.STEEL,
        rot=(0.0, 0.0, math.radians(24.0)))
kit.box("FrogHouse", (1.1, 0.9, 0.5), (0.0, 0.2, 5.72), kit.CHARCOAL)
kit.cyl("Actuator", 0.09, 0.8, (0.0, 0.85, 5.72), kit.STEEL, axis="Y",
        verts=10)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=9.5,
                                         height=5.0)

# ---- carrier turntable: floor platter with drive housing ----
NAME = "SM_LB_Paint_CarrierTurntable_v001"
kit.reset(); kit.glass_material()
kit.box("Plinth", (4.5, 3.4, 0.25), (0.0, 0.0, 0.125), kit.GREEN)
kit.cyl("PlatterRing", 1.55, 0.30, (0.0, 0.0, 0.40), kit.CHARCOAL,
        verts=28)
kit.cyl("Platter", 1.45, 0.35, (0.0, 0.0, 0.55), kit.STEEL, verts=28)
kit.box("TrackStub", (2.8, 0.5, 0.30), (0.0, 0.0, 0.95), kit.STEEL)
kit.box("DriveHouse", (0.8, 0.6, 0.6), (1.95, 1.25, 0.55), kit.GREEN)
kit.box("EStop", (0.12, 0.06, 0.12), (1.95, 0.94, 0.85), kit.RED)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=6.5,
                                         height=2.2)

# ---- body skid: runner rails, cross tubes, locator cones ----
NAME = "SM_LB_Paint_BodySkidCarrier_v001"
kit.reset(); kit.glass_material()
for sy in (-0.95, 0.95):
    kit.box("Runner", (5.0, 0.22, 0.28), (0.0, sy, 0.14), kit.STEEL)
    kit.box("WearStrip", (5.0, 0.10, 0.04), (0.0, sy, 0.30),
            kit.CHARCOAL, chamfer=False)
for cx in (-2.1, -0.7, 0.7, 2.1):
    kit.cyl("CrossTube", 0.07, 1.9, (cx, 0.0, 0.30), kit.GREEN,
            axis="Y", verts=10)
for cx in (-1.85, 1.85):
    for sy in (-0.95, 0.95):
        kit.cyl("LocatorCone", 0.09, 0.5, (cx, sy, 0.56), kit.RED,
                verts=10)
for ex in (-2.42, 2.42):
    kit.box("LiftPocket", (0.16, 1.9, 0.14), (ex, 0.0, 0.36),
            kit.CHARCOAL)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=5.5,
                                         height=1.6)
print("BATCH07 COMPLETE")
