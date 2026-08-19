"""Paint sludge dewatering skid: the filter press for booth scrubber sludge.

Recognised by the row of vertical press plates on tie bars between heavy
end plates, the hydraulic closer with its cylinder, the sludge skip below
the plate pack, and the feed pipe arriving at the fixed end.
"""
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, RED, STEEL, WARMWHITE, YELLOW, box,
                          cyl, export, preview, reset)

reset()

box("Skid", (3.0, 1.1, 0.12), (0, 0, 0.06), CHARCOAL)
for sx in (-1.3, 1.3):
    box("Stand", (0.22, 0.9, 0.65), (sx, 0, 0.44), GREEN)

# End plates, tie bars, and the press plate pack.
box("FixedEnd", (0.16, 0.9, 1.0), (-1.15, 0, 1.26), CHARCOAL)
box("MovingEnd", (0.14, 0.85, 0.95), (0.55, 0, 1.26), CHARCOAL)
for ty in (-0.36, 0.36):
    for tz in (0.9, 1.62):
        cyl("TieBar", 0.035, 2.6, (-0.1, ty, tz), STEEL, axis="X", verts=10)
for n in range(11):
    box("PressPlate", (0.06, 0.8, 0.9), (-0.95 + n * 0.14, 0, 1.26), GREEN,
        chamfer=False)

# Hydraulic closer at the moving end.
cyl("CloserCyl", 0.12, 0.7, (1.05, 0, 1.26), CHARCOAL, axis="X", verts=16)
cyl("CloserRod", 0.05, 0.35, (0.72, 0, 1.26), STEEL, axis="X", verts=10)
box("CloserFrame", (0.16, 0.9, 1.0), (1.35, 0, 1.26), GREEN)
box("PowerPack", (0.5, 0.4, 0.4), (1.3, 0, 0.32), GREEN)
cyl("PackMotor", 0.09, 0.25, (1.3, 0.3, 0.32), CHARCOAL, axis="Y", verts=12)

# Sludge skip under the pack and the feed pipe at the fixed end.
box("Skip", (1.6, 0.8, 0.5), (-0.35, 0, 0.42), STEEL)
box("SkipLip", (1.65, 0.85, 0.05), (-0.35, 0, 0.68), CHARCOAL, chamfer=False)
cyl("FeedPipe", 0.06, 1.2, (-1.45, 0.2, 1.9), STEEL, verts=12)
cyl("FeedElbow", 0.06, 0.35, (-1.32, 0.2, 2.45), STEEL, axis="X", verts=12)
cyl("FeedValve", 0.09, 0.05, (-1.45, 0.2, 1.55), YELLOW, axis="Y", verts=12)
box("IDPlate", (0.02, 0.2, 0.11), (-1.51, -0.2, 0.9), WARMWHITE,
    chamfer=False)

export("SM_LB_Paint_SludgeDewateringSkid_v001", "PaintShop/SludgeSkid_v001")
preview("SM_LB_Paint_SludgeDewateringSkid_v001", "PaintShop/SludgeSkid_v001")
