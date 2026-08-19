"""Paint PF conveyor switch: the track junction that diverts carriers.

Matches the goalpost track family: the through track box carries on,
a branch box diverges in plan, and the switch machine with its moving
tongue and position flag sits over the frog point.
"""
import math
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, STEEL, WARMWHITE, box, column, cyl,
                          export, preview, reset)

reset()

for sy in (-1.7, 1.7):
    column("Post", (0, sy, 0), 5.35, GREEN, width=0.30)
box("Bridge", (0.55, 3.8, 0.34), (0, 0, 5.70), GREEN)

# Through track and the diverging branch.
box("TrackBox", (4.0, 0.32, 0.26), (0, 0, 5.33), CHARCOAL)
for sy in (-0.12, 0.12):
    box("SlotFlange", (4.0, 0.08, 0.05), (0, sy, 5.17), STEEL, chamfer=False)
BRANCH = math.radians(28.0)
box("BranchBox", (2.6, 0.32, 0.26),
    (1.05, 0.62, 5.33), CHARCOAL, rot=(0.0, 0.0, BRANCH))
box("BranchFlange", (2.6, 0.08, 0.05),
    (1.05, 0.5, 5.17), STEEL, rot=(0.0, 0.0, BRANCH), chamfer=False)

# Switch machine over the frog with tongue and position flag.
box("SwitchMachine", (0.7, 0.5, 0.3), (0.1, 0.3, 5.62), GREEN)
box("Tongue", (0.6, 0.08, 0.1), (0.25, 0.18, 5.38), STEEL,
    rot=(0.0, 0.0, BRANCH * 0.5), chamfer=False)
cyl("FlagPost", 0.02, 0.3, (0.1, 0.3, 5.9), STEEL, verts=8)
box("Flag", (0.14, 0.02, 0.1), (0.17, 0.3, 6.02), WARMWHITE, chamfer=False)
box("JunctionGusset", (0.4, 0.14, 0.3), (0.55, 0.36, 5.5), CHARCOAL,
    rot=(0.0, 0.0, BRANCH))
# Butt plates so the three open ends read as chaining to the next segment,
# and a hanger strut carrying the branch off the bridge.
for ex in (-1.99, 1.99):
    box("ButtPlate", (0.03, 0.40, 0.36), (ex, 0, 5.33), CHARCOAL,
        chamfer=False)
box("BranchButt", (0.03, 0.40, 0.36), (2.19, 1.23, 5.33), CHARCOAL,
    rot=(0.0, 0.0, BRANCH), chamfer=False)
box("BranchHanger", (0.08, 0.08, 0.34), (1.6, 0.95, 5.55), STEEL,
    rot=(math.radians(35.0), 0.0, BRANCH), chamfer=False)
box("IDPlate", (0.02, 0.20, 0.12), (0.16, -1.86, 2.4), WARMWHITE,
    chamfer=False)

export("SM_LB_Paint_PFSwitch_v001", "PaintShop/PFSwitch_v001")
preview("SM_LB_Paint_PFSwitch_v001", "PaintShop/PFSwitch_v001")
