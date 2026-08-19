"""Paint booth scrubber trench: the under-booth wash that catches
overspray.

Recognised by the open trench module with its grating walkway strips,
the weir plates across the water channel, the eliminator baffle bank
rising at the back, and the sludge drag chain sprocket at the drive end.
Chains end to end under a booth.
"""
import math
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, STEEL, WARMWHITE, box, cyl, export,
                          preview, reset)

reset()

# Trench tub with end plates.
box("TubFloor", (3.6, 1.6, 0.08), (0, 0, 0.04), CHARCOAL)
for sy in (-0.78, 0.78):
    box("TubWall", (3.6, 0.06, 0.6), (0, sy, 0.3), GREEN)
for ex in (-1.78, 1.78):
    box("TubEnd", (0.06, 1.6, 0.6), (ex, 0, 0.3), GREEN)

# Water surface and weir plates across the channel.
box("Water", (3.4, 1.35, 0.02), (0, -0.06, 0.3), STEEL, chamfer=False)
for wx in (-1.0, 0.0, 1.0):
    box("Weir", (0.04, 1.35, 0.26), (wx, -0.06, 0.42), STEEL, chamfer=False)

# Grating walkway strips along both rims.
for sy in (-0.68, 0.68):
    box("WalkStrip", (3.6, 0.24, 0.05), (0, sy, 0.62), CHARCOAL)
    for n in range(12):
        box("Grate", (0.02, 0.22, 0.06), (-1.65 + n * 0.3, sy, 0.63), STEEL,
            chamfer=False)

# Eliminator baffle bank rising at the north rim.
for n in range(8):
    box("Baffle", (0.35, 0.05, 0.7), (-1.4 + n * 0.4, 0.55, 0.98), STEEL,
        rot=(math.radians(25.0), 0.0, 0.0), chamfer=False)
box("BaffleHeader", (3.4, 0.1, 0.1), (0, 0.42, 1.31), GREEN)

# Sludge drag chain drive at the east end.
cyl("DragSprocket", 0.18, 0.08, (1.7, -0.06, 0.35), CHARCOAL, axis="Y",
    verts=16)
box("DriveHouse", (0.35, 0.3, 0.35), (1.86, -0.06, 0.72), GREEN)
cyl("DriveMotor", 0.09, 0.28, (1.86, 0.15, 0.72), STEEL, axis="Y", verts=12)
box("Placard", (0.02, 0.22, 0.12), (-1.82, 0, 0.45), WARMWHITE,
    chamfer=False)

export("SM_LB_Paint_BoothScrubberTrench_v001",
       "PaintShop/BoothScrubberTrench_v001")
preview("SM_LB_Paint_BoothScrubberTrench_v001",
        "PaintShop/BoothScrubberTrench_v001")
