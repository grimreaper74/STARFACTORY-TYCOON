"""Paint pipe bridge module: carries services between plant rooms and line.

Recognised by the two trestle towers, the pipe rack level with mixed-bore
runs on saddles, the cable tray level above, and the drip guard beneath.
6 m span that chains end to end.
"""
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, STEEL, WARMWHITE, box, column, cyl,
                          export, preview, reset)

reset()

for sx in (-2.8, 2.8):
    column("Tower", (sx, 0, 0), 4.2, GREEN, width=0.26)

# Pipe rack level with mixed-bore runs on saddle beams.
for bx in (-2.4, 0.0, 2.4):
    box("Saddle", (0.12, 1.3, 0.12), (bx, 0, 3.6), CHARCOAL)
box("RackBeam", (6.0, 0.14, 0.14), (0, -0.6, 3.55), GREEN)
box("RackBeam2", (6.0, 0.14, 0.14), (0, 0.6, 3.55), GREEN)
for py, pr in ((-0.45, 0.09), (-0.2, 0.06), (0.05, 0.06), (0.3, 0.12),
               (0.55, 0.04)):
    cyl("Pipe", pr, 6.0, (0, py, 3.72), STEEL, axis="X", verts=12)

# Cable tray level and the drip guard.
box("TrayBeam", (6.0, 0.10, 0.08), (0, 0, 4.35), GREEN)
box("CableTray", (6.0, 0.5, 0.07), (0, 0, 4.45), CHARCOAL)
box("TrayCover", (6.0, 0.44, 0.02), (0, 0, 4.50), STEEL, chamfer=False)
box("DripGuard", (5.6, 1.2, 0.03), (0, 0, 3.30), STEEL, chamfer=False)
# Hanger rods so the guard reads as hung off the rack beams, not floating.
for hx in (-2.0, 2.0):
    for hy in (-0.5, 0.5):
        cyl("GuardHanger", 0.02, 0.32, (hx, hy, 3.44), CHARCOAL, verts=8)
box("IDPlate", (0.2, 0.02, 0.11), (-2.8, -0.15, 2.2), WARMWHITE, chamfer=False)

export("SM_LB_Paint_PipeBridge_Module_v001", "PaintShop/PipeBridge_v001")
preview("SM_LB_Paint_PipeBridge_Module_v001", "PaintShop/PipeBridge_v001")
