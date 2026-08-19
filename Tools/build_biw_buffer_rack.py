"""Weld BIW buffer rack: a stackable body stillage for the P17 buffer.

Recognised by the forkable base frame, four cornered posts with stacking
cones, the two cradle beams with wear pads that take the body sills, and
the cross-braced rear face.
"""
import math
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, STEEL, WARMWHITE, YELLOW, box, cyl,
                          export, preview, reset)

reset()

# Forkable base frame.
for ry in (-0.8, 0.8):
    box("BaseRail", (4.8, 0.16, 0.12), (0, ry, 0.06), CHARCOAL)
for cx in (-1.9, 0.0, 1.9):
    box("BaseCross", (0.14, 1.76, 0.10), (cx, 0, 0.17), CHARCOAL)
for fx in (-0.9, 0.9):
    box("ForkPocket", (0.16, 2.0, 0.14), (fx, 0, 0.10), STEEL)

# Corner posts with stacking cones and base gussets.
for px in (-2.2, 2.2):
    for py in (-0.8, 0.8):
        box("Post", (0.14, 0.14, 1.9), (px, py, 1.07), GREEN)
        cyl("StackCone", 0.05, 0.14, (px, py, 2.07), STEEL, verts=12)
        box("PostGusset", (0.10, 0.05, 0.22),
            (px + (0.10 if px < 0 else -0.10), py, 0.23), CHARCOAL)

# Cradle beams on stanchions, wear pads where the sills land.
for bx in (-1.5, 1.5):
    box("CradleBeam", (0.16, 1.9, 0.12), (bx, 0, 1.0), CHARCOAL)
    for py in (-0.8, 0.8):
        box("Stanchion", (0.12, 0.12, 0.82), (bx, py, 0.53), CHARCOAL)
    for py in (-0.7, 0.7):
        box("WearPad", (0.22, 0.26, 0.06), (bx, py, 1.09), YELLOW)

# Side rails and full-span rear cross bracing between the posts.
for py in (-0.8, 0.8):
    box("SideRail", (4.26, 0.08, 0.08), (0, py, 1.75), GREEN)
brace = math.hypot(4.26, 0.65)
for sign in (1.0, -1.0):
    box("RearBrace", (brace, 0.05, 0.05), (0, 0.8, 1.375), STEEL,
        rot=(0.0, sign * math.atan2(0.65, 4.26), 0.0), chamfer=False)
box("Placard", (0.34, 0.02, 0.2), (-2.2, -0.89, 1.5), WARMWHITE,
    chamfer=False)

export("SM_LB_Weld_BIWBufferRack_v001", "WeldShop/BIWBufferRack_v001")
preview("SM_LB_Weld_BIWBufferRack_v001", "WeldShop/BIWBufferRack_v001")
