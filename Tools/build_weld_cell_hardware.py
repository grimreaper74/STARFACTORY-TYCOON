"""Two high-count weld cell machines: electrode tip dresser and geometry pin unit.

Both are compact, which the pedestal welder showed is where detail reads best per part.
The tip dresser sits beside every robot (one per arm, so 36 plus); the geo pin unit
repeats 56 plus across the shop fixtures, so detail here multiplies further than
anywhere else in weld.
"""
import math
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, RED, STEEL, WARMWHITE, YELLOW, box,
                          column, cyl, export, preview, reset)

# ---------------------------------------------------------------------------
# 1. Electrode tip dresser. A robot presents its gun to the cutter head; swarf
#    drops down the chute into the bin. Recognised by the cutter, the chute and
#    the drive motor hung off the side.
# ---------------------------------------------------------------------------
reset()
box("Base", (0.48, 0.48, 0.14), (0, 0, 0.07), CHARCOAL)
box("BaseSkirt", (0.56, 0.56, 0.04), (0, 0, 0.02), YELLOW)
column("Stand", (0, 0, 0.14), 0.8, GREEN, width=0.17)

# Dresser head: housing, cutter with a bored centre, and the guard ring.
box("Head", (0.36, 0.32, 0.28), (0, 0, 1.1), GREEN)
box("HeadCover", (0.38, 0.06, 0.24), (0, -0.15, 1.1), CHARCOAL, chamfer=False)
cyl("Cutter", 0.08, 0.09, (0, 0, 1.29), STEEL)
cyl("CutterBore", 0.036, 0.11, (0, 0, 1.33), CHARCOAL, verts=12)
cyl("GuardRing", 0.11, 0.03, (0, 0, 1.25), YELLOW)

# Belt-driven motor hung off the side, with its pulley cover.
cyl("Motor", 0.09, 0.26, (-0.28, 0, 1.06), CHARCOAL, axis="X")
cyl("MotorFan", 0.07, 0.05, (-0.42, 0, 1.06), STEEL, axis="X")
box("BeltCover", (0.22, 0.14, 0.2), (-0.14, 0, 1.06), GREEN)
box("Terminal", (0.09, 0.08, 0.08), (-0.28, 0.11, 1.14), CHARCOAL)

# Swarf chute into a removable bin, plus the air blast line.
box("Chute", (0.13, 0.16, 0.42), (0.2, 0, 0.86), STEEL,
    rot=(0.0, math.radians(20.0), 0.0))
box("Bin", (0.28, 0.28, 0.26), (0.34, 0, 0.27), YELLOW)
box("BinLip", (0.31, 0.31, 0.03), (0.34, 0, 0.41), CHARCOAL)
cyl("AirLine", 0.016, 0.44, (0.1, 0.13, 1.0), STEEL)
cyl("EStop", 0.05, 0.05, (-0.09, -0.18, 0.72), RED, axis="Y")

export("SM_LB_Weld_TipDresser_v001", "WeldShop/TipDresser_v001")
preview("SM_LB_Weld_TipDresser_v001", "WeldShop/TipDresser_v001")

# ---------------------------------------------------------------------------
# 2. Geometry pin unit. Locates a panel on a fixture. Recognised by the pin
#    itself, the adjustable shim stack under the block, and the proximity
#    sensor that confirms the panel is seated.
# ---------------------------------------------------------------------------
reset()
box("Base", (0.32, 0.32, 0.08), (0, 0, 0.04), CHARCOAL)
for bx in (-1.0, 1.0):
    for by in (-1.0, 1.0):
        cyl("Bolt", 0.018, 0.05, (bx * 0.11, by * 0.11, 0.075), STEEL, verts=10)

# Riser with webs, then the shim stack that makes it adjustable.
box("Riser", (0.2, 0.2, 0.32), (0, 0, 0.24), GREEN)
for sign in (1.0, -1.0):
    box("Web", (0.035, 0.19, 0.24), (sign * 0.11, 0, 0.23), CHARCOAL, chamfer=False)
for n in range(3):
    box("Shim", (0.23, 0.21, 0.012), (0, 0, 0.41 + n * 0.014), STEEL, chamfer=False)

# Locating block, tapered pin and its bush.
box("Block", (0.25, 0.23, 0.15), (0, 0, 0.51), STEEL)
box("BlockFace", (0.26, 0.04, 0.16), (0, -0.11, 0.51), CHARCOAL, chamfer=False)
cyl("Bush", 0.042, 0.06, (0, 0, 0.6), CHARCOAL)
cyl("Pin", 0.026, 0.28, (0, 0, 0.73), STEEL)
cyl("PinTip", 0.017, 0.08, (0, 0, 0.9), YELLOW)

# Proximity sensor on its bracket, with the cable dropping to a connector.
box("SensorBracket", (0.05, 0.13, 0.05), (0.11, 0.08, 0.56), CHARCOAL)
cyl("Sensor", 0.021, 0.09, (0.15, 0.12, 0.56), RED, axis="Y")
cyl("SensorCable", 0.01, 0.24, (0.15, 0.12, 0.44), STEEL)
box("Connector", (0.04, 0.04, 0.06), (0.15, 0.12, 0.31), WARMWHITE)

export("SM_LB_Weld_GeoPinUnit_v001", "WeldShop/GeoPinUnit_v001")
preview("SM_LB_Weld_GeoPinUnit_v001", "WeldShop/GeoPinUnit_v001")
