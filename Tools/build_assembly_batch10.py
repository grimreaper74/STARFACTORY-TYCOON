"""Journey batch 10 - assembly chassis and marriage stations.

Heavy marriage gantry, the floor marriage table (v001), chassis
hanger, ergonomic scissor platform, urethane pump, fluid fill,
the HVAC module part and the glass A-frame rack.
Original names into DetailUplift for the standard swap.
"""
import math
import sys

sys.path.append(r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
import bpy  # noqa: E402
import lb_model_kit as kit  # noqa: E402


def out(name):
    return "DetailUplift_v001/" + name


# ---- heavy marriage gantry: screw-jack lift portal ----
NAME = "SM_LB_Assembly_HeavyMarriageGantry_v001"
kit.reset(); kit.glass_material()
for sx in (-2.75, 2.75):
    for sy in (-2.15, 2.15):
        kit.box("Post", (0.35, 0.35, 5.3), (sx, sy, 2.65), kit.GREEN)
        kit.box("BasePlate", (0.55, 0.55, 0.1), (sx, sy, 0.05),
                kit.CHARCOAL)
for sy in (-2.15, 2.15):
    kit.box("TopBeam", (5.9, 0.4, 0.45), (0.0, sy, 5.35), kit.GREEN)
kit.box("LiftBeam", (5.5, 3.6, 0.35), (0.0, 0.0, 4.3), kit.STEEL)
for sx in (-2.2, 2.2):
    for sy in (-1.4, 1.4):
        kit.cyl("ScrewJack", 0.09, 1.1, (sx, sy, 4.95), kit.CHARCOAL,
                verts=10)
kit.box("ToolPlate", (4.2, 2.6, 0.16), (0.0, 0.0, 4.05), kit.GREEN)
for px in (-1.7, 1.7):
    for py in (-1.0, 1.0):
        kit.cyl("LocatorPin", 0.05, 0.35, (px, py, 3.85), kit.RED,
                verts=8)
kit.box("FestoonTray", (5.8, 0.18, 0.12), (0.0, -2.35, 5.0),
        kit.CHARCOAL)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=10.5,
                                         height=5.0)

# ---- powertrain marriage v001: floor lift-table station ----
NAME = "SM_LB_Assembly_PowertrainMarriage_v001"
kit.reset(); kit.glass_material()
kit.box("BaseFrame", (6.3, 4.7, 0.3), (0.0, 0.0, 0.15), kit.GREEN)
for sx in (-1.7, 1.7):
    kit.box("LiftTable", (2.1, 1.7, 0.22), (sx, -0.9, 1.5), kit.STEEL)
    kit.scissor("TableScissor", (sx, -0.9, 0.8), 1.7, 1.15,
                kit.CHARCOAL)
    for px in (-0.7, 0.7):
        kit.cyl("EnginePedestal", 0.11, 0.7, (sx + px, -0.9, 1.95),
                kit.CHARCOAL, verts=10)
kit.box("BatteryCradle", (3.4, 1.5, 0.35), (0.0, 1.35, 1.05),
        kit.GREEN)
for bx in (-1.3, 0.0, 1.3):
    kit.box("CradleRib", (0.12, 1.55, 0.42), (bx, 1.35, 1.05),
            kit.CHARCOAL)
kit.box("ServoCab", (0.9, 0.5, 1.5), (2.85, 1.95, 0.9), kit.GREEN)
kit.box("SideRail", (6.2, 0.12, 0.35), (0.0, -2.28, 0.45), kit.STEEL)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=10.0,
                                         height=3.2)

# ---- chassis hanger: overhead twin-yoke carrier ----
NAME = "SM_LB_Assembly_ChassisHanger_v001"
kit.reset(); kit.glass_material()
for tx in (-0.7, 0.7):
    kit.box("Trolley", (0.45, 0.2, 0.16), (tx, 0.0, 2.0),
            kit.CHARCOAL)
    kit.cyl("TrolleyWheel", 0.07, 0.06, (tx, 0.0, 2.1), kit.STEEL,
            axis="Y", verts=12)
kit.box("SpreaderBeam", (2.3, 0.18, 0.18), (0.0, 0.0, 1.85),
        kit.GREEN)
for sx in (-0.95, 0.95):
    kit.box("DropArm", (0.12, 0.12, 1.1), (sx, 0.0, 1.25), kit.GREEN)
    kit.box("YokeArm", (0.14, 1.5, 0.14), (sx, 0.0, 0.72), kit.GREEN)
    for sy in (-0.65, 0.65):
        kit.box("CradlePad", (0.3, 0.22, 0.1), (sx, sy, 0.62),
                kit.CHARCOAL)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=4.0,
                                         height=1.8)

# ---- ergonomic lift platform: body scissor deck ----
NAME = "SM_LB_Assembly_ErgonomicLiftPlatform_v001"
kit.reset(); kit.glass_material()
kit.box("BaseFrame", (5.4, 2.7, 0.2), (0.0, 0.0, 0.1), kit.GREEN)
kit.scissor("DeckScissor", (-1.3, 0.0, 0.65), 2.2, 0.85, kit.CHARCOAL)
kit.scissor("DeckScissor2", (1.3, 0.0, 0.65), 2.2, 0.85, kit.CHARCOAL)
kit.box("Deck", (5.4, 2.7, 0.14), (0.0, 0.0, 1.18), kit.STEEL)
kit.box("EdgeStrip", (5.4, 0.08, 0.06), (0.0, 1.31, 1.28), kit.YELLOW,
        chamfer=False)
kit.box("EdgeStrip", (5.4, 0.08, 0.06), (0.0, -1.31, 1.28), kit.YELLOW,
        chamfer=False)
for px in (-2.0, 2.0):
    for py in (-0.85, 0.85):
        kit.cyl("BodyLocator", 0.07, 0.3, (px, py, 1.4), kit.RED,
                verts=8)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=7.0,
                                         height=2.0)

# ---- urethane pump unit: glazing adhesive skid ----
NAME = "SM_LB_Assembly_UrethanePumpUnit_v001"
kit.reset(); kit.glass_material()
kit.box("Frame", (3.05, 0.95, 0.15), (0.0, 0.0, 0.075), kit.GREEN)
for i, dx in enumerate((-1.0, -0.2)):
    kit.cyl("Drum", 0.28, 0.95, (dx, 0.0, 0.62), kit.STEEL, verts=16)
    kit.cyl("Follower", 0.24, 0.5, (dx, 0.0, 1.35), kit.CHARCOAL,
            verts=16)
    kit.cyl("PumpMast", 0.06, 1.3, (dx, 0.0, 2.2), kit.GREEN, verts=8)
kit.box("MixerBlock", (0.5, 0.4, 0.5), (0.8, 0.0, 1.6), kit.CHARCOAL)
kit.cyl("HoseReel", 0.35, 0.18, (1.35, 0.0, 2.5), kit.GREEN, axis="Y",
        verts=18)
kit.box("PanelBox", (0.5, 0.3, 0.7), (1.3, 0.0, 0.6), kit.GREEN)
kit.box("HeadBeam", (3.0, 0.14, 0.14), (0.0, 0.0, 2.85), kit.STEEL)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=4.8,
                                         height=2.6)

# ---- fluid fill machine: cabinet with fill boom ----
NAME = "SM_LB_Assembly_FluidFillMachine_v001"
kit.reset(); kit.glass_material()
kit.box("Cabinet", (1.5, 1.0, 1.7), (0.0, 0.0, 0.85), kit.GREEN)
kit.box("DoorSeam", (0.04, 0.8, 1.4), (0.76, 0.0, 0.85), kit.CHARCOAL,
        chamfer=False)
kit.cyl("SightColumn", 0.08, 1.4, (-0.55, 0.42, 0.9), kit.GLASS,
        verts=12)
kit.box("BoomArm", (1.1, 0.12, 0.12), (0.5, 0.0, 1.85), kit.STEEL)
kit.cyl("FillCoupler", 0.09, 0.35, (1.05, 0.0, 1.62), kit.CHARCOAL,
        verts=10)
for i in range(3):
    kit.cyl("ValveKnob", 0.06, 0.08, (-0.3 + i * 0.3, -0.52,
            1.45), kit.RED, verts=8, axis="Y")
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=3.2,
                                         height=1.8)

# ---- HVAC module: blower + heater core part ----
NAME = "SM_LB_Assembly_HVACModule_v001"
kit.reset(); kit.glass_material()
kit.box("CoreBox", (0.55, 0.5, 0.5), (-0.1, 0.0, 0.35), kit.CHARCOAL)
kit.cyl("BlowerScroll", 0.22, 0.3, (0.28, 0.05, 0.4), kit.GREEN,
        axis="Y", verts=16)
kit.cyl("DuctStub", 0.09, 0.2, (-0.1, 0.0, 0.68), kit.STEEL, verts=10)
kit.cyl("DuctStub2", 0.07, 0.18, (-0.35, 0.2, 0.5), kit.STEEL,
        axis="X", verts=10)
kit.box("Flange", (0.5, 0.06, 0.4), (-0.1, -0.28, 0.35), kit.STEEL,
        chamfer=False)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=1.6,
                                         height=0.7)

# ---- glass A-frame rack: leaned windscreen stack ----
NAME = "SM_LB_Assembly_GlassAFrameRack_v001"
kit.reset(); kit.glass_material()
kit.box("BaseRail", (2.1, 1.3, 0.12), (0.0, 0.0, 0.06), kit.GREEN)
for sx in (-0.95, 0.95):
    kit.box("ALeg", (0.1, 0.1, 1.75), (sx, -0.3, 0.9), kit.GREEN,
            rot=(math.radians(14.0), 0.0, 0.0))
    kit.box("ALeg2", (0.1, 0.1, 1.75), (sx, 0.3, 0.9), kit.GREEN,
            rot=(math.radians(-14.0), 0.0, 0.0))
kit.box("TopBar", (2.1, 0.1, 0.1), (0.0, 0.0, 1.78), kit.GREEN)
for i in range(3):
    off = -0.42 + i * 0.09
    kit.box("GlassPane", (1.7, 0.03, 1.15), (0.0, off, 0.72),
            kit.GLASS, rot=(math.radians(-14.0), 0.0, 0.0),
            chamfer=False)
for py in (-0.5, 0.5):
    kit.box("LeanPad", (1.9, 0.06, 0.1), (0.0, py, 0.14),
            kit.CHARCOAL)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=3.6,
                                         height=1.7)
print("BATCH10 COMPLETE")
