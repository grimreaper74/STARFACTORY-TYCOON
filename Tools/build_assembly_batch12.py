"""Journey batch 12 - assembly's last four: leak test, EOL, storage.

Water leak test booth (spray rings over a drain lane), end-of-line
inspection arch, flash gantry and the heavy store bay racking.
Completes the assembly kit. Original names into DetailUplift.
"""
import math
import sys

sys.path.append(r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
import bpy  # noqa: E402
import lb_model_kit as kit  # noqa: E402


def out(name):
    return "DetailUplift_v001/" + name


# ---- water leak test booth: spray tunnel with roof tank ----
NAME = "SM_LB_Assembly_WaterLeakTestBooth_v001"
kit.reset(); kit.glass_material()
kit.box("FloorPan", (15.7, 8.0, 0.2), (0.0, 0.0, 0.1), kit.CHARCOAL)
kit.box("DrainLane", (15.7, 3.0, 0.06), (0.0, 0.0, 0.24), kit.STEEL)
for sy in (-3.9, 3.9):
    kit.box("SideWall", (15.8, 0.15, 3.6), (0.0, sy, 1.9), kit.GREEN)
    for i in range(7):
        kit.box("WallSeam", (0.06, 0.2, 3.4), (-6.6 + i * 2.2, sy,
                1.85), kit.CHARCOAL, chamfer=False)
kit.box("Roof", (15.8, 8.03, 0.25), (0.0, 0.0, 3.83), kit.GREEN)
for ex in (-7.83, 7.83):
    kit.box("EndFrame", (0.15, 8.0, 4.0), (ex, 0.0, 2.0), kit.GREEN)
    kit.box("EndAperture", (0.12, 3.4, 3.2), (ex, 0.0, 1.6),
            kit.CHARCOAL, chamfer=False)
for rx in (-4.5, 0.0, 4.5):
    for sy in (-1.9, 1.9):
        kit.cyl("SprayLeg", 0.07, 3.2, (rx, sy, 1.7), kit.STEEL,
                verts=10)
    kit.cyl("SprayArch", 0.07, 3.9, (rx, 0.0, 3.3), kit.STEEL,
            axis="Y", verts=10)
    for ny in (-1.2, -0.4, 0.4, 1.2):
        kit.cyl("Nozzle", 0.03, 0.14, (rx, ny, 3.18), kit.CHARCOAL,
                verts=6)
kit.box("RoofTank", (3.4, 2.2, 1.0), (-4.5, 0.0, 4.46), kit.STEEL)
kit.box("PumpHouse", (1.6, 1.2, 0.8), (-1.8, 0.0, 4.36), kit.GREEN)
kit.cyl("SupplyPipe", 0.10, 5.6, (1.2, 0.0, 4.2), kit.STEEL, axis="X",
        verts=10)
kit.cyl("PipeDrop", 0.10, 0.5, (3.95, 0.0, 3.95), kit.STEEL, verts=10)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=20.0,
                                         height=5.5)

# ---- EOL inspection arch: instrumented goalpost ----
NAME = "SM_LB_Assembly_EOLInspectionArch_v001"
kit.reset(); kit.glass_material()
for sy in (-1.75, 1.75):
    kit.column("Leg", (0.0, sy, 0.0), 3.3, kit.GREEN, width=0.2)
kit.box("ArchBeam", (0.24, 3.7, 0.3), (0.0, 0.0, 3.45), kit.GREEN)
for py in (-1.1, 0.0, 1.1):
    kit.box("CameraPod", (0.3, 0.26, 0.24), (0.0, py, 3.2),
            kit.CHARCOAL)
    kit.cyl("Lens", 0.05, 0.14, (0.0, py, 3.02), kit.STEEL, verts=10)
for sy in (-1.45, 1.45):
    kit.box("SideSensor", (0.22, 0.08, 1.6), (0.0, sy, 1.9),
            kit.CHARCOAL)
    kit.box("SensorStrip", (0.14, 0.04, 1.4), (0.0, sy - 0.06
            if sy > 0 else sy + 0.06, 1.9), kit.WARMWHITE,
            chamfer=False)
kit.box("EBox", (0.5, 0.4, 0.9), (0.0, 1.95, 0.5), kit.GREEN)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=6.0,
                                         height=3.0)

# ---- flash gantry: lamp row over the line ----
NAME = "SM_LB_Assembly_FlashGantry_v001"
kit.reset(); kit.glass_material()
for sy in (-2.2, 2.2):
    kit.box("Leg", (0.14, 0.14, 3.6), (0.0, sy, 1.8), kit.GREEN)
kit.box("Beam", (0.2, 4.5, 0.24), (0.0, 0.0, 3.72), kit.GREEN)
for py in (-1.8, -0.9, 0.0, 0.9, 1.8):
    kit.box("FlashHead", (0.32, 0.5, 0.2), (0.0, py, 3.5),
            kit.CHARCOAL)
    kit.box("FlashLens", (0.26, 0.42, 0.05), (0.0, py, 3.38),
            kit.WARMWHITE, chamfer=False)
kit.box("CableDrop", (0.08, 0.08, 3.4), (0.0, 2.14, 1.9),
        kit.CHARCOAL)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=6.5,
                                         height=3.2)

# ---- store bay: heavy pallet racking with stock ----
NAME = "SM_LB_Assembly_StoreBay_v001"
kit.reset(); kit.glass_material()
for sx in (-2.45, 0.0, 2.45):
    for sy in (-2.25, 2.25):
        kit.box("Upright", (0.14, 0.14, 4.6), (sx, sy, 2.3),
                kit.GREEN)
    kit.box("CrossTie", (0.1, 4.5, 0.1), (sx, 0.0, 4.5), kit.GREEN)
for level_z in (1.5, 3.0, 4.4):
    for sy in (-2.15, 2.15):
        kit.box("BeamRail", (5.1, 0.12, 0.16), (0.0, sy, level_z),
                kit.STEEL)
for bay_x in (-1.25, 1.25):
    for level_z in (1.58, 3.08):
        kit.box("PalletBlank", (1.9, 4.3, 0.12), (bay_x, 0.0,
                level_z + 0.06), kit.CHARCOAL, chamfer=False)
        kit.box("StockBox", (1.6, 3.8, 0.85), (bay_x, 0.0,
                level_z + 0.55), kit.STEEL if bay_x < 0 else
                kit.GREEN)
kit.box("FloorStock", (1.7, 3.9, 0.9), (-1.25, 0.0, 0.45),
        kit.CHARCOAL)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=9.0,
                                         height=4.2)
print("BATCH12 COMPLETE")
