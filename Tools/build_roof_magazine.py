"""Weld shop roof-panel magazine: slotted rack the loading robot picks from.

A panel magazine is recognised by its comb rails full of thin panels standing
shoulder to shoulder, the A-frame ends that carry the combs, and the forklift
pockets and docking cones that say it gets swapped as a unit. A few empty
slots read as a magazine mid-shift rather than a display rack.
"""
import math
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, RED, STEEL, WARMWHITE, YELLOW, box,
                          cyl, export, preview, reset)

reset()

# ---- base skids with forklift pockets and docking cones ---------------------
for sy in (-0.55, 0.55):
    box("Skid", (2.5, 0.16, 0.12), (0, sy, 0.06), CHARCOAL)
for cx in (-1.05, 0.0, 1.05):
    box("SkidCross", (0.14, 1.20, 0.10), (cx, 0, 0.07), CHARCOAL)
for px in (-0.55, 0.55):
    box("ForkPocket", (0.24, 1.30, 0.15), (px, 0, 0.10), CHARCOAL)
    box("ForkMouth", (0.20, 0.03, 0.11), (px, -0.66, 0.10), YELLOW,
        chamfer=False)
for dx in (-1.15, 1.15):
    cyl("DockCone", 0.045, 0.10, (dx, -0.62, 0.05), STEEL, verts=12)

# ---- A-frame ends with edge posts -------------------------------------------
for sx in (-1.15, 1.15):
    box("EndWall", (0.09, 1.05, 1.45), (sx, 0, 0.86), GREEN)
    for sy in (-0.55, 0.55):
        box("EndPost", (0.13, 0.13, 1.55), (sx, sy, 0.90), CHARCOAL)
    box("EndCap", (0.16, 1.20, 0.08), (sx, 0, 1.70), CHARCOAL)
    # Rib and X-brace so the end sheet reads fabricated, not blank.
    box("EndRib", (0.12, 1.05, 0.06), (sx, 0, 0.86), CHARCOAL)
    for bs in (-1.0, 1.0):
        box("EndBrace", (0.05, 1.05, 0.09), (sx + 0.06 * (1 if sx > 0 else -1),
            0, 0.86), CHARCOAL, rot=(bs * 0.72, 0.0, 0.0))
box("IDPlate", (0.02, 0.34, 0.22), (-1.21, 0, 1.30), WARMWHITE, chamfer=False)

# ---- comb rails and their fins ----------------------------------------------
for sy in (-0.42, 0.42):
    box("CombRail", (2.2, 0.09, 0.09), (0, sy, 0.24), GREEN)
    for n in range(11):
        fx = -1.0 + n * 0.2
        box("CombFin", (0.025, 0.07, 0.30), (fx, sy, 0.42), STEEL,
            chamfer=False)

# ---- roof panels leaning in the slots, two slots empty ----------------------
for n in (0, 1, 2, 4, 5, 7, 8, 9):
    px = -0.90 + n * 0.2
    box("RoofPanel", (0.035, 1.10, 1.30), (px, 0, 0.88), STEEL,
        rot=(0.0, math.radians(11.0), 0.0), chamfer=False)

# ---- top ties and a contents sensor -----------------------------------------
for sy in (-0.50, 0.50):
    box("TopTie", (2.35, 0.09, 0.07), (0, sy, 1.66), GREEN)
box("SensorBracket", (0.03, 0.05, 0.14), (1.19, -0.30, 1.55), STEEL,
    chamfer=False)
box("Sensor", (0.05, 0.04, 0.05), (1.21, -0.30, 1.62), YELLOW, chamfer=False)
cyl("EndConduit", 0.018, 1.3, (1.20, 0.45, 0.85), STEEL, verts=10)
box("EndJBox", (0.10, 0.14, 0.16), (1.21, 0.45, 1.55), GREEN)

export("SM_LB_Weld_RoofMagazine_v001", "WeldShop/RoofMagazine_v001")
preview("SM_LB_Weld_RoofMagazine_v001", "WeldShop/RoofMagazine_v001")
