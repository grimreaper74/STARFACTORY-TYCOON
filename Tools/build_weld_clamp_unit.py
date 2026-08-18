"""Weld clamp unit - the power clamp that holds a panel to a fixture. 72 plus
placements across the weld gates and fixtures, the highest-count machine in the shop.
Recognised by its pivoting arm with a swan-neck finger, the pneumatic cylinder driving
it, and the open-state sensor block.
"""
import math
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, RED, STEEL, WARMWHITE, YELLOW, box,
                          cyl, export, preview, reset)

reset()
# Bolted base and body.
box("Base", (0.26, 0.2, 0.06), (0, 0, 0.03), CHARCOAL)
for bx in (-1.0, 1.0):
    cyl("Bolt", 0.015, 0.04, (bx * 0.09, 0.055, 0.065), STEEL, verts=10)
    cyl("Bolt2", 0.015, 0.04, (bx * 0.09, -0.055, 0.065), STEEL, verts=10)
box("Body", (0.16, 0.14, 0.3), (0, 0, 0.21), GREEN)
box("BodyRib", (0.18, 0.03, 0.26), (0, 0.075, 0.2), CHARCOAL, chamfer=False)

# Pneumatic cylinder angled into the back of the body.
cyl("Cylinder", 0.055, 0.24, (-0.16, 0, 0.14), CHARCOAL, axis="X")
cyl("CylPort", 0.016, 0.06, (-0.26, 0.04, 0.18), STEEL, axis="Y", verts=10)
cyl("CylRod", 0.018, 0.1, (-0.045, 0, 0.17), STEEL, axis="X")

# Pivot boss and the clamp arm with its swan-neck finger and pad.
cyl("Pivot", 0.045, 0.2, (0, 0, 0.38), STEEL, axis="Y")
box("Arm", (0.3, 0.05, 0.07), (0.13, 0, 0.42), STEEL,
    rot=(0.0, math.radians(-18.0), 0.0))
box("Finger", (0.12, 0.05, 0.06), (0.29, 0, 0.51), STEEL,
    rot=(0.0, math.radians(35.0), 0.0))
cyl("Pad", 0.032, 0.045, (0.33, 0, 0.55), YELLOW)

# Fixed lower jaw so the clamp closes onto something.
box("Jaw", (0.12, 0.09, 0.08), (0.28, 0, 0.3), GREEN)
cyl("JawPad", 0.032, 0.035, (0.31, 0, 0.36), CHARCOAL)

# Sensor block with two indicator windows and its cable.
box("SensorBlock", (0.07, 0.06, 0.1), (-0.02, -0.09, 0.42), CHARCOAL)
box("SensorWin", (0.05, 0.012, 0.02), (-0.02, -0.125, 0.45), RED, chamfer=False)
box("SensorWin2", (0.05, 0.012, 0.02), (-0.02, -0.125, 0.41), WARMWHITE,
    chamfer=False)
cyl("Cable", 0.008, 0.3, (-0.02, -0.09, 0.24), STEEL)

export("SM_LB_Weld_ClampUnit_v001", "WeldShop/ClampUnit_v001")
preview("SM_LB_Weld_ClampUnit_v001", "WeldShop/ClampUnit_v001")
