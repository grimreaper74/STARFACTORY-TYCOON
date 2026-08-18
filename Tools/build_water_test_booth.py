"""Assembly water leak test booth: the enclosed spray tunnel at line end.

Recognised by its ribbed tunnel shell with open drive-through ends, the
interior spray arches with nozzle rows visible through them, floor drainage
grates the full length, the pump skid against one wall and the tank behind.
Ribs and portals keep the long walls from reading as blank slabs.
"""
import math
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, STEEL, WARMWHITE, YELLOW, box, cyl,
                          export, preview, reset)

reset()

L, W, H = 14.0, 6.0, 5.0

# Portal frames every 2 m carry the shell.
for n in range(8):
    px = -6.3 + n * 1.8
    for sy in (-W * 0.5, W * 0.5):
        box("PortalLeg", (0.22, 0.22, H - 0.6), (px, sy, (H - 0.6) * 0.5),
            CHARCOAL)
    box("PortalHead", (0.22, W + 0.2, 0.30), (px, 0, H - 0.45), CHARCOAL)

# Wall and roof panels between portals - inset so the ribs shadow them.
for sy in (-W * 0.5, W * 0.5):
    box("WallPanel", (L, 0.08, 4.35), (0, sy, 2.48), GREEN)
    box("WallBand", (L, 0.10, 0.22), (0, sy, 2.48), CHARCOAL, chamfer=False)
    box("WallBandHigh", (L, 0.10, 0.22), (0, sy, 3.95), CHARCOAL,
        chamfer=False)
box("Roof", (L, W + 0.1, 0.10), (0, 0, H - 0.25), GREEN)
box("RoofRidge", (L, 0.5, 0.16), (0, 0, H - 0.14), CHARCOAL)

# Open ends with marked aprons and strip-curtain hints.
for ex, s in ((-L * 0.5, 1.0), (L * 0.5, -1.0)):
    box("EndApron", (0.8, 3.4, 0.04), (ex + s * -0.5, 0, 0.02), YELLOW,
        chamfer=False)
    for n in range(7):
        box("Curtain", (0.02, 0.38, 2.3), (ex, -1.35 + n * 0.45, 3.0),
            WARMWHITE, chamfer=False)

# Interior spray arches with nozzle studs, visible through the ends.
for ax in (-4.2, -1.4, 1.4, 4.2):
    for sy in (-1.9, 1.9):
        box("SprayLeg", (0.14, 0.14, 3.4), (ax, sy, 1.7), STEEL)
    box("SprayHead", (0.14, 4.0, 0.14), (ax, 0, 3.45), STEEL)
    for n in range(7):
        cyl("Nozzle", 0.03, 0.10, (ax, -1.65 + n * 0.55, 3.32), CHARCOAL,
            verts=8)

# Floor drainage grates the full length, both sides of the track.
for sy in (-1.15, 1.15):
    for n in range(9):
        box("DrainGrate", (1.4, 0.5, 0.03), (-5.8 + n * 1.45, sy, 0.015),
            STEEL, chamfer=False)

# Pump skid and water tank against the south wall.
box("PumpSkid", (2.2, 1.0, 0.15), (-3.0, -W * 0.5 - 0.85, 0.075), CHARCOAL)
for pn in range(2):
    cyl("Pump", 0.28, 0.8, (-3.6 + pn * 1.2, -W * 0.5 - 0.85, 0.5), GREEN,
        axis="X", verts=16)
    cyl("PumpMotor", 0.20, 0.45, (-3.0 + pn * 1.2, -W * 0.5 - 0.85, 0.5),
        CHARCOAL, axis="X", verts=16)
cyl("Tank", 0.9, 2.4, (1.5, -W * 0.5 - 1.0, 1.2), GREEN, verts=24)
cyl("TankLid", 0.92, 0.08, (1.5, -W * 0.5 - 1.0, 2.44), CHARCOAL, verts=24)
cyl("FeedPipe", 0.06, 3.2, (-0.4, -W * 0.5 - 0.9, 0.9), STEEL, axis="X",
    verts=10)
cyl("RiserPipe", 0.06, 2.6, (-3.0, -W * 0.5 - 0.4, 1.9), STEEL, verts=10)

export("SM_LB_Assembly_WaterLeakTestBooth_v001", "AssemblyShop/WaterTest_v001")
preview("SM_LB_Assembly_WaterLeakTestBooth_v001", "AssemblyShop/WaterTest_v001")
