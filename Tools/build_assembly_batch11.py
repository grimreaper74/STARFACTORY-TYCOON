"""Journey batch 11 - assembly final line: wheels, alignment, gauges.

Wheel carousel and rack (real dished wheels from the kit), alignment
bed with roller plates, headlamp aim rig, closure fit gauge and the
two sequenced carts. Original names into DetailUplift for the swap.
"""
import math
import sys

sys.path.append(r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
import bpy  # noqa: E402
import lb_model_kit as kit  # noqa: E402


def out(name):
    return "DetailUplift_v001/" + name


# ---- wheel carousel: two-tier rotary buffer ----
NAME = "SM_LB_Assembly_WheelCarousel_v001"
kit.reset(); kit.glass_material()
kit.cyl("DriveBase", 0.9, 0.3, (0.0, 0.0, 0.15), kit.GREEN, verts=20)
kit.cyl("Column", 0.18, 2.6, (0.0, 0.0, 1.45), kit.STEEL, verts=14)
for tier_z in (0.55, 1.75):
    kit.cyl("TierPlate", 2.0, 0.1, (0.0, 0.0, tier_z), kit.CHARCOAL,
            verts=16)
    kit.cyl("TierRim", 2.05, 0.05, (0.0, 0.0, tier_z + 0.07),
            kit.GREEN, verts=16)
for i, (wx, wy) in enumerate(((-1.3, -1.05), (1.3, -1.05),
                              (-1.3, 1.05), (1.3, 1.05))):
    kit.cyl("LowerTire", 0.36, 0.24, (wx, wy, 0.96), kit.TIRE,
            axis="Y", verts=24)
    kit.cyl("LowerHub", 0.14, 0.26, (wx, wy, 0.96), kit.STEEL,
            axis="Y", verts=14)
for i, (wx, wy) in enumerate(((-1.05, 0.0), (1.05, 0.0))):
    kit.cyl("UpperTire", 0.36, 0.24, (wx, wy, 2.25), kit.TIRE,
            axis="Y", verts=24)
    kit.cyl("UpperHub", 0.14, 0.26, (wx, wy, 2.25), kit.STEEL,
            axis="Y", verts=14)
kit.box("MotorBox", (0.6, 0.45, 0.4), (0.75, 0.0, 0.35), kit.GREEN)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=7.0,
                                         height=2.6)

# ---- wheel and tire rack: two shelves of wheels ----
NAME = "SM_LB_Assembly_WheelTireRack_v001"
kit.reset(); kit.glass_material()
for sx in (-1.1, 1.1):
    kit.box("EndFrame", (0.1, 1.05, 1.75), (sx, 0.0, 0.9), kit.GREEN)
for sz in (0.12, 0.95):
    kit.box("Shelf", (2.3, 1.0, 0.07), (0.0, 0.0, sz), kit.STEEL)
for i, wx in enumerate((-0.75, -0.25, 0.25, 0.75)):
    kit.cyl("LowTire", 0.36, 0.24, (wx, 0.0, 0.52), kit.TIRE,
            axis="X", verts=24)
    kit.cyl("LowHub", 0.14, 0.26, (wx, 0.0, 0.52), kit.STEEL,
            axis="X", verts=14)
for i, wx in enumerate((-0.5, 0.5)):
    kit.cyl("TopTire", 0.36, 0.24, (wx, 0.0, 1.35), kit.TIRE,
            axis="X", verts=24)
    kit.cyl("TopHub", 0.14, 0.26, (wx, 0.0, 1.35), kit.STEEL,
            axis="X", verts=14)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=3.8,
                                         height=1.7)

# ---- wheel alignment bed: roller plates + console ----
NAME = "SM_LB_Assembly_WheelAlignmentBed_v001"
kit.reset(); kit.glass_material()
kit.box("Bed", (5.3, 2.7, 0.45), (0.0, 0.0, 0.225), kit.GREEN)
for ex in (-2.72, 2.72):
    kit.box("Ramp", (0.35, 2.6, 0.3), (ex, 0.0, 0.15), kit.CHARCOAL,
            rot=(0.0, math.radians(-18.0 if ex > 0 else 18.0), 0.0))
for px in (-1.55, 1.55):
    for py in (-0.85, 0.85):
        kit.box("RollerPlate", (0.95, 0.7, 0.08), (px, py, 0.5),
                kit.STEEL)
        for rx in (-0.28, 0.28):
            kit.cyl("Roller", 0.07, 0.6, (px + rx, py, 0.52),
                    kit.CHARCOAL, axis="Y", verts=12)
kit.box("CenterConsole", (0.9, 0.5, 0.35), (0.0, 0.0, 0.62),
        kit.STEEL)
kit.box("SensorPost", (0.1, 0.1, 0.6), (0.0, 1.28, 0.9), kit.GREEN)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=7.0,
                                         height=2.0)

# ---- headlamp aim rig: sliding tower on floor rails ----
NAME = "SM_LB_Assembly_HeadlampAimRig_v001"
kit.reset(); kit.glass_material()
for ry in (-1.4, 1.4):
    kit.box("FloorRail", (3.3, 0.16, 0.1), (0.0, ry, 0.05), kit.GREEN)
kit.box("Slide", (0.9, 2.9, 0.18), (-0.9, 0.0, 0.2), kit.STEEL)
kit.box("Tower", (0.35, 0.35, 1.3), (-0.9, 0.0, 0.9), kit.GREEN)
for by in (-0.55, 0.55):
    kit.box("AimBox", (0.45, 0.6, 0.5), (-0.9, by, 1.3), kit.CHARCOAL)
    kit.box("AimLens", (0.04, 0.42, 0.36), (-0.65, by, 1.3), kit.GLASS,
            chamfer=False)
kit.box("CounterBase", (0.8, 0.7, 0.3), (-0.9, 0.0, 0.32),
        kit.CHARCOAL)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=4.6,
                                         height=1.6)

# ---- closure fit gauge: C-frame with sensor pods ----
NAME = "SM_LB_Assembly_ClosureFitGauge_v001"
kit.reset(); kit.glass_material()
kit.box("Pedestal", (0.6, 0.55, 0.9), (0.0, 0.0, 0.45), kit.GREEN)
kit.box("CPost", (0.2, 0.2, 1.2), (-0.6, 0.0, 1.45), kit.STEEL)
kit.box("CArm", (1.5, 0.18, 0.18), (0.1, 0.0, 2.05), kit.STEEL)
for i, ax in enumerate((-0.25, 0.25, 0.72)):
    kit.box("SensorPod", (0.16, 0.14, 0.2), (ax, 0.0, 1.9),
            kit.CHARCOAL)
    kit.cyl("ProbeTip", 0.025, 0.16, (ax, 0.0, 1.74), kit.RED,
            verts=8)
kit.box("EBox", (0.4, 0.3, 0.4), (0.0, 0.0, 1.1), kit.CHARCOAL)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=3.0,
                                         height=1.8)

# ---- sequenced parts cart: tugger with shelves ----
NAME = "SM_LB_Assembly_SequencedPartsCart_v001"
kit.reset(); kit.glass_material()
kit.box("Chassis", (1.75, 1.05, 0.1), (0.0, 0.0, 0.2), kit.GREEN)
for cx in (-0.7, 0.7):
    for cy in (-0.4, 0.4):
        kit.cyl("Caster", 0.09, 0.07, (cx, cy, 0.1), kit.CHARCOAL,
                axis="Y", verts=12)
for pz in (0.65, 1.1, 1.55):
    kit.box("Shelf", (1.7, 1.0, 0.05), (0.0, 0.0, pz), kit.STEEL)
for px in (-0.83, 0.83):
    for py in (-0.48, 0.48):
        kit.box("Post", (0.06, 0.06, 1.4), (px, py, 0.9), kit.GREEN)
kit.box("TowHitch", (0.25, 0.08, 0.08), (1.0, 0.0, 0.28),
        kit.CHARCOAL)
for i in range(3):
    kit.box("BinBlank", (0.5, 0.9, 0.28), (-0.55 + i * 0.55, 0.0,
            0.85), kit.CHARCOAL, chamfer=False)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=3.2,
                                         height=1.5)

# ---- shield cart: underbody panels stacked flat ----
NAME = "SM_LB_Assembly_ShieldCart_v001"
kit.reset(); kit.glass_material()
kit.box("Frame", (1.85, 1.08, 0.12), (0.0, 0.0, 0.25), kit.GREEN)
for cx in (-0.75, 0.75):
    for cy in (-0.42, 0.42):
        kit.cyl("Caster", 0.08, 0.07, (cx, cy, 0.12), kit.CHARCOAL,
                axis="Y", verts=12)
for i in range(4):
    kit.box("ShieldPanel", (1.6, 0.95, 0.05), (0.0, 0.0, 0.38 + i
            * 0.09), kit.STEEL if i % 2 else kit.CHARCOAL,
            chamfer=False)
for px in (-0.88, 0.88):
    kit.box("EndStop", (0.08, 1.0, 0.6), (px, 0.0, 0.6), kit.GREEN)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=3.2,
                                         height=1.2)
print("BATCH11 COMPLETE")
