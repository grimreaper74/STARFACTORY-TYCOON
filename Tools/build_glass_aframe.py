"""Assembly glass A-frame rack: windscreens staged for the glazing robots.

Recognised by the A-profile with rubber-lined battens, the row of glass
panes leaning on each face, the kick frame with castors, and the push
handle. Glass reads as thin steel-grey panes with a top edge highlight.
"""
import math
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, STEEL, WARMWHITE, YELLOW, box, cyl,
                          export, preview, reset)

reset()

LEAN = math.radians(12.0)

# Kick frame with castors and push handle.
box("KickFrame", (2.10, 1.10, 0.10), (0, 0, 0.17), GREEN)
for cx in (-0.9, 0.9):
    for cy in (-0.42, 0.42):
        cyl("Castor", 0.06, 0.05, (cx, cy, 0.06), CHARCOAL, axis="Y",
            verts=12)
        box("CastorFork", (0.05, 0.08, 0.08), (cx, cy, 0.12), STEEL,
            chamfer=False)
cyl("Handle", 0.02, 1.0, (-1.08, 0, 0.95), STEEL, axis="Y", verts=10)
for hy in (-0.45, 0.45):
    cyl("HandlePost", 0.02, 0.75, (-1.08, hy, 0.58), STEEL, verts=10)

# A-frame: two leaning faces with rubber battens and a crest cap.
for s in (-1.0, 1.0):
    box("Face", (2.00, 0.07, 1.55), (0, s * 0.28, 0.98), GREEN,
        rot=(s * LEAN, 0.0, 0.0))
    for bz in (0.45, 1.05, 1.55):
        off = s * (0.28 - math.tan(LEAN) * (bz - 0.98))
        box("Batten", (2.00, 0.09, 0.07), (0, off, bz), CHARCOAL,
            chamfer=False)
box("CrestCap", (2.05, 0.30, 0.08), (0, 0, 1.80), CHARCOAL)

# Glass panes leaning on both faces, one slot spare per side.
for s in (-1.0, 1.0):
    for n in range(3):
        py = s * (0.42 + n * 0.075)
        box("Glass", (1.55 - n * 0.1, 0.02, 1.05), (0, py, 0.95), STEEL,
            rot=(s * LEAN, 0.0, 0.0), chamfer=False)
        box("GlassEdge", (1.55 - n * 0.1, 0.022, 0.03),
            (0, py - s * math.tan(LEAN) * 0.52, 1.47), WARMWHITE,
            rot=(s * LEAN, 0.0, 0.0), chamfer=False)
box("IDPlate", (0.02, 0.20, 0.12), (1.02, 0, 0.85), WARMWHITE, chamfer=False)

export("SM_LB_Assembly_GlassAFrameRack_v001", "AssemblyShop/GlassAFrame_v001")
preview("SM_LB_Assembly_GlassAFrameRack_v001", "AssemblyShop/GlassAFrame_v001")
