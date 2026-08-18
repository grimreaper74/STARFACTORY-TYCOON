"""Paint spray applicator end effector for the booth robots.

A rotary-bell applicator is recognised by its tapering body from the robot
flange, the bell cup at the tip, the air-shroud ring behind it, and the
paint and air lines dressed along the body. Flange pivot at the origin so it
mounts where the robot's tool adapter expects.
"""
import math
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, STEEL, WARMWHITE, box, cyl, export,
                          preview, reset)

reset()

# Mounting flange with bolt ring, then the tapering body along +X.
cyl("Flange", 0.075, 0.03, (0.015, 0, 0), STEEL, axis="X", verts=20)
for n in range(6):
    a = n * math.pi / 3.0
    cyl("FlangeBolt", 0.008, 0.02, (0.005, 0.055 * math.cos(a),
        0.055 * math.sin(a)), CHARCOAL, axis="X", verts=8)
box("Adapter", (0.06, 0.09, 0.09), (0.06, 0, 0), CHARCOAL)
cyl("BodyRear", 0.055, 0.14, (0.16, 0, 0), GREEN, axis="X", verts=18)
cyl("BodyMid", 0.045, 0.12, (0.28, 0, 0), GREEN, axis="X", verts=18)
cyl("ShroudRing", 0.052, 0.03, (0.345, 0, 0), CHARCOAL, axis="X", verts=18)
cyl("BellNeck", 0.028, 0.06, (0.385, 0, 0), STEEL, axis="X", verts=14)
cyl("BellCup", 0.048, 0.035, (0.425, 0, 0), WARMWHITE, axis="X", verts=20)
cyl("BellRim", 0.052, 0.012, (0.445, 0, 0), STEEL, axis="X", verts=20)

# Paint and air lines dressed along the body into the adapter.
for sy, sz in ((0.045, 0.02), (-0.045, 0.02), (0.0, -0.05)):
    cyl("Line", 0.009, 0.30, (0.20, sy, sz), CHARCOAL, axis="X", verts=8)
    cyl("LineFit", 0.013, 0.03, (0.075, sy, sz), STEEL, axis="X", verts=8)
box("ValveBlock", (0.05, 0.07, 0.05), (0.13, 0, -0.06), CHARCOAL)
box("IDTag", (0.03, 0.001, 0.02), (0.16, -0.056, 0.03), WARMWHITE,
    chamfer=False)

export("SM_LB_Paint_SprayApplicatorTool_v001",
       "PaintShop/SprayApplicator_v001")
preview("SM_LB_Paint_SprayApplicatorTool_v001", "PaintShop/SprayApplicator_v001")
