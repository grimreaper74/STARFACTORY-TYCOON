"""Journey batch 8 - paint's last twelve: services, skids and tools.

AHU, extraction, scrubber trench, dosing/mix/UF/sludge skids, burner
house, oven stack, service set and the two robot end effectors.
Lights-out plant: no ladders or walk platforms - conduit and flanges
instead. Original names into DetailUplift for the standard swap.
"""
import math
import sys

sys.path.append(r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
import bpy  # noqa: E402
import lb_model_kit as kit  # noqa: E402


def out(name):
    return "DetailUplift_v001/" + name


def skid_frame(length, depth, height=0.18):
    kit.box("SkidRail", (length, 0.12, height), (0.0, depth / 2.0 - 0.06,
            height / 2.0), kit.GREEN)
    kit.box("SkidRail", (length, 0.12, height), (0.0, -depth / 2.0 + 0.06,
            height / 2.0), kit.GREEN)
    kit.box("SkidDeck", (length, depth, 0.06), (0.0, 0.0, height + 0.03),
            kit.CHARCOAL, chamfer=False)


# ---- AHU module: sectioned air handler ----
NAME = "SM_LB_Paint_AHU_Module_v001"
kit.reset(); kit.glass_material()
kit.box("Base", (4.4, 1.75, 0.15), (0.0, 0.0, 0.075), kit.CHARCOAL)
kit.box("Casing", (4.4, 1.72, 2.2), (0.0, 0.0, 1.25), kit.STEEL)
for sx in (-1.45, 0.0, 1.45):
    kit.box("SectionSeam", (0.05, 1.78, 2.1), (sx, 0.0, 1.25),
            kit.CHARCOAL, chamfer=False)
kit.box("Louvre", (0.06, 1.3, 1.5), (-2.18, 0.0, 1.3), kit.CHARCOAL)
for i in range(5):
    kit.box("LouvreFin", (0.08, 1.25, 0.06), (-2.19, 0.0, 0.75 + i
            * 0.28), kit.STEEL, chamfer=False)
for dx in (-0.7, 0.7):
    kit.box("PanelHandle", (0.04, 0.05, 0.22), (dx, -0.89, 1.2),
            kit.GREEN)
kit.cyl("FanScroll", 0.55, 0.7, (1.45, 0.0, 2.35), kit.GREEN, axis="Y",
        verts=20)
kit.cyl("Discharge", 0.35, 0.4, (1.45, 0.0, 2.62), kit.STEEL, verts=14)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=6.5,
                                         height=2.6)

# ---- air extraction module: cabinet + tall cowled stack ----
NAME = "SM_LB_Paint_AirExtractionModule_v001"
kit.reset(); kit.glass_material()
kit.box("Cabinet", (3.35, 2.4, 2.4), (0.0, 0.0, 1.2), kit.STEEL)
kit.box("DoorSeam", (0.04, 1.0, 1.9), (1.69, -0.5, 1.2), kit.CHARCOAL,
        chamfer=False)
kit.box("InletFlange", (0.5, 0.9, 0.9), (-1.85, 0.0, 1.5), kit.GREEN)
kit.cyl("StackBody", 0.62, 1.5, (0.6, 0.0, 3.15), kit.STEEL, verts=20)
kit.cyl("StackCowl", 0.75, 0.25, (0.6, 0.0, 4.0), kit.CHARCOAL,
        verts=20)
kit.box("Conduit", (0.08, 0.08, 2.3), (1.62, 0.9, 1.35), kit.CHARCOAL)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=7.0,
                                         height=3.8)

# ---- booth scrubber trench: grated water trough ----
NAME = "SM_LB_Paint_BoothScrubberTrench_v001"
kit.reset(); kit.glass_material()
kit.box("Trough", (3.85, 1.6, 0.9), (0.0, 0.0, 0.45), kit.CHARCOAL)
kit.box("WaterFace", (3.65, 1.4, 0.06), (0.0, 0.0, 0.88), kit.GLASS,
        chamfer=False)
for i in range(6):
    kit.box("GratingStrip", (0.55, 1.55, 0.05), (-1.6 + i * 0.64, 0.0,
            0.98), kit.STEEL, chamfer=False)
for wx in (-1.2, 0.0, 1.2):
    kit.box("WeirPlate", (0.05, 1.5, 0.35), (wx, 0.0, 1.15), kit.GREEN,
            chamfer=False)
kit.cyl("DrainPipe", 0.09, 3.6, (0.0, 0.72, 0.25), kit.STEEL, axis="X",
        verts=10)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=5.5,
                                         height=1.6)

# ---- chem dosing skid: three tanks, pumps, manifold ----
NAME = "SM_LB_Paint_ChemDosingSkid_v001"
kit.reset(); kit.glass_material()
skid_frame(3.4, 1.38)
for i, tx in enumerate((-1.15, 0.0, 1.15)):
    kit.cyl("DosingTank", 0.42, 1.15, (tx, 0.15, 0.85), kit.GREEN if
            i != 1 else kit.STEEL, verts=18)
    kit.cyl("TankLid", 0.30, 0.12, (tx, 0.15, 1.48), kit.CHARCOAL,
            verts=14)
    kit.cyl("DosingPump", 0.10, 0.30, (tx, -0.48, 0.39), kit.CHARCOAL,
            verts=10)
kit.cyl("Manifold", 0.06, 3.2, (0.0, -0.55, 0.75), kit.STEEL, axis="X",
        verts=10)
for vx in (-1.15, 0.0, 1.15):
    kit.cyl("Valve", 0.08, 0.08, (vx, -0.55, 0.9), kit.RED, verts=10)
kit.box("ControlBox", (0.45, 0.18, 0.6), (1.55, -0.55, 1.3), kit.GREEN)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=5.0,
                                         height=2.0)

# ---- mix room skid: agitated pots ----
NAME = "SM_LB_Paint_MixRoomSkid_v001"
kit.reset(); kit.glass_material()
skid_frame(2.4, 1.2)
for tx in (-0.6, 0.6):
    kit.cyl("MixPot", 0.45, 1.3, (tx, 0.0, 0.95), kit.STEEL, verts=18)
    kit.cyl("PotBand", 0.47, 0.10, (tx, 0.0, 1.35), kit.GREEN,
            verts=18)
    kit.cyl("AgitatorMotor", 0.16, 0.45, (tx, 0.0, 1.85),
            kit.CHARCOAL, verts=12)
    kit.cyl("FeedPipe", 0.05, 0.8, (tx, 0.45, 1.9), kit.STEEL,
            axis="Y", verts=8)
kit.box("PipeRack", (2.3, 0.08, 0.08), (0.0, 0.80, 1.9), kit.STEEL)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=4.5,
                                         height=2.2)

# ---- oven burner house: burner box + gas train ----
NAME = "SM_LB_Paint_OvenBurnerHouse_v001"
kit.reset(); kit.glass_material()
kit.box("House", (3.25, 2.6, 2.6), (0.0, 0.0, 1.4), kit.STEEL)
kit.box("Louvre", (0.06, 1.6, 1.4), (-1.64, 0.0, 1.4), kit.CHARCOAL)
kit.cyl("BurnerSnout", 0.35, 0.9, (1.95, 0.0, 1.5), kit.GREEN,
        axis="X", verts=16)
kit.cyl("SnoutFlange", 0.45, 0.15, (2.35, 0.0, 1.5), kit.CHARCOAL,
        axis="X", verts=16)
for i in range(3):
    kit.cyl("GasTrain", 0.07, 2.4, (0.0, -1.42, 0.5 + i * 0.45),
            kit.STEEL, axis="X", verts=8)
    kit.cyl("GasValve", 0.10, 0.10, (-0.4 + i * 0.4, -1.42,
            0.65 + i * 0.45), kit.RED, verts=8)
kit.cyl("StackStub", 0.30, 0.8, (0.0, 0.0, 3.0), kit.STEEL, verts=16)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=6.0,
                                         height=3.0)

# ---- oven stack: braced tower + flue ----
NAME = "SM_LB_Paint_OvenStack_v001"
kit.reset(); kit.glass_material()
for sx in (-1.55, 1.55):
    for sy in (-1.35, 1.35):
        kit.column("TowerLeg", (sx, sy, 0.0), 4.0, kit.GREEN,
                   width=0.16)
for z in (1.4, 2.8, 4.0):
    kit.box("BraceRing", (3.25, 0.10, 0.12), (0.0, 1.35, z), kit.GREEN)
    kit.box("BraceRing", (3.25, 0.10, 0.12), (0.0, -1.35, z),
            kit.GREEN)
    kit.box("BraceRing", (0.10, 2.85, 0.12), (1.55, 0.0, z), kit.GREEN)
    kit.box("BraceRing", (0.10, 2.85, 0.12), (-1.55, 0.0, z),
            kit.GREEN)
kit.cyl("Flue", 0.70, 7.9, (0.0, 0.0, 3.95), kit.STEEL, verts=24)
kit.cyl("MidFlange", 0.78, 0.15, (0.0, 0.0, 4.4), kit.CHARCOAL,
        verts=24)
kit.cyl("TopRim", 0.78, 0.25, (0.0, 0.0, 8.15), kit.CHARCOAL, verts=24)
kit.box("Conduit", (0.07, 0.07, 7.6), (0.75, 0.0, 3.8), kit.CHARCOAL)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=13.0,
                                         height=6.5)

# ---- sealer nozzle tool: robot end effector ----
NAME = "SM_LB_Paint_SealerNozzleTool_v001"
kit.reset(); kit.glass_material()
kit.cyl("MountFlange", 0.13, 0.04, (0.0, 0.0, 0.48), kit.CHARCOAL,
        verts=16)
kit.box("Body", (0.24, 0.20, 0.26), (0.0, 0.0, 0.32), kit.STEEL,
        chamfer=False)
kit.cyl("NozzleBarrel", 0.045, 0.18, (0.0, 0.0, 0.14), kit.GREEN,
        verts=10)
kit.cyl("Needle", 0.015, 0.09, (0.0, 0.0, 0.03), kit.CHARCOAL,
        verts=8)
kit.cyl("MaterialLine", 0.03, 0.22, (0.10, 0.0, 0.42), kit.RED,
        axis="X", verts=8)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=1.1,
                                         height=0.5)

# ---- service set: transformer, valve station, manifold ----
NAME = "SM_LB_Paint_ServiceSet_v001"
kit.reset(); kit.glass_material()
kit.box("TxBox", (1.1, 0.9, 1.25), (-1.1, 0.55, 0.68), kit.GREEN)
for i in range(6):
    kit.box("TxFin", (1.0, 0.03, 0.9), (-1.1, 0.98 + i * 0.012, 0.72),
            kit.STEEL, chamfer=False)
kit.box("JunctionCab", (0.7, 0.35, 1.0), (-1.2, -0.6, 0.55), kit.STEEL)
for i, vx in enumerate((0.35, 0.85, 1.35)):
    kit.cyl("Riser", 0.07, 1.2, (vx, 0.55, 0.6), kit.STEEL, verts=8)
    kit.cyl("RiserValve", 0.10, 0.09, (vx, 0.55, 1.28), kit.RED,
            verts=8)
kit.cyl("Manifold", 0.09, 2.4, (0.5, -0.5, 1.0), kit.STEEL, axis="X",
        verts=10)
for px in (-0.3, 0.5, 1.3):
    kit.box("PipeStand", (0.08, 0.08, 1.0), (px, -0.5, 0.5), kit.GREEN)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=5.0,
                                         height=1.8)

# ---- sludge dewatering skid: plate press ----
NAME = "SM_LB_Paint_SludgeDewateringSkid_v001"
kit.reset(); kit.glass_material()
skid_frame(3.05, 1.08)
kit.box("HeadStand", (0.22, 0.9, 1.7), (-1.35, 0.0, 1.05), kit.GREEN)
kit.box("TailStand", (0.22, 0.9, 1.7), (1.35, 0.0, 1.05), kit.GREEN)
kit.box("TopBeam", (2.9, 0.16, 0.16), (0.0, 0.0, 1.95), kit.GREEN)
for i in range(11):
    kit.box("PressPlate", (0.09, 0.85, 0.95), (-1.05 + i * 0.19, 0.0,
            1.15), kit.STEEL, chamfer=False)
kit.cyl("Ram", 0.16, 0.7, (1.7, 0.0, 1.15), kit.CHARCOAL, axis="X",
        verts=14)
kit.box("SludgeTray", (2.4, 0.95, 0.18), (0.0, 0.0, 0.33),
        kit.CHARCOAL)
kit.cyl("FeedPipe", 0.07, 2.9, (0.0, 0.0, 2.15), kit.STEEL, axis="X",
        verts=8)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=5.0,
                                         height=2.4)

# ---- spray applicator tool: bell atomiser ----
NAME = "SM_LB_Paint_SprayApplicatorTool_v001"
kit.reset(); kit.glass_material()
kit.cyl("MountFlange", 0.075, 0.03, (-0.20, 0.0, 0.08), kit.CHARCOAL,
        axis="X", verts=14)
kit.cyl("BodyBarrel", 0.065, 0.26, (-0.05, 0.0, 0.08), kit.STEEL,
        axis="X", verts=14)
kit.cyl("BellNeck", 0.04, 0.10, (0.12, 0.0, 0.08), kit.GREEN,
        axis="X", verts=12)
kit.cyl("BellCup", 0.07, 0.06, (0.20, 0.0, 0.08), kit.CHARCOAL,
        axis="X", verts=14)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=1.0,
                                         height=0.25)

# ---- UF membrane skid: stacked membrane tubes ----
NAME = "SM_LB_Paint_UFMembraneSkid_v001"
kit.reset(); kit.glass_material()
skid_frame(2.65, 1.08)
for i in range(3):
    mz = 0.55 + i * 0.5
    kit.cyl("MembraneTube", 0.16, 2.3, (0.0, 0.15, mz), kit.STEEL,
            axis="X", verts=14)
    kit.cyl("EndCap", 0.18, 0.12, (-1.2, 0.15, mz), kit.GREEN,
            axis="X", verts=14)
    kit.cyl("EndCap", 0.18, 0.12, (1.2, 0.15, mz), kit.GREEN, axis="X",
            verts=14)
kit.cyl("CrossPipe", 0.05, 1.1, (-1.15, 0.15, 1.05), kit.CHARCOAL,
        verts=8)
kit.cyl("FeedPump", 0.14, 0.4, (0.9, -0.38, 0.40), kit.GREEN, verts=12)
kit.box("PanelBox", (0.4, 0.16, 0.5), (-0.9, -0.42, 0.55), kit.GREEN)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=4.5,
                                         height=1.8)
print("BATCH08 COMPLETE")
