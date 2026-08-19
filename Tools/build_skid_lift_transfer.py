"""Weld skid lift transfer: the P18 scissor table with a roller bed that
hands the finished body-in-white across to paint.

Recognised by the scissor linkage under a rollered platform with side
guards and end stops, and the control pedestal at the corner.
"""
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, STEEL, WARMWHITE, box, cyl, export,
                          preview, reset, scissor)

reset()

box("BaseFrame", (2.2, 1.4, 0.12), (0, 0, 0.06), CHARCOAL)
scissor("Lift", (0, 0, 0.62), 1.7, 0.9, GREEN)
box("Platform", (2.2, 1.4, 0.1), (0, 0, 1.12), GREEN)
for n in range(8):
    cyl("Roller", 0.05, 1.3, (-0.91 + n * 0.26, 0, 1.22), STEEL, axis="Y",
        verts=12)
for gy in (-0.68, 0.68):
    box("SideGuard", (2.2, 0.05, 0.14), (0, gy, 1.24), GREEN)
for ex in (-1.08, 1.08):
    box("EndStop", (0.06, 1.3, 0.18), (ex, 0, 1.26), CHARCOAL)

# Control pedestal at the south-east corner.
box("PedBase", (0.24, 0.24, 0.05), (1.35, -0.5, 0.03), CHARCOAL)
box("PedPost", (0.08, 0.08, 1.0), (1.35, -0.5, 0.55), GREEN)
box("PedPanel", (0.26, 0.06, 0.2), (1.35, -0.53, 1.12), WARMWHITE)
box("IDPlate", (0.02, 0.22, 0.12), (-1.11, 0, 0.9), WARMWHITE, chamfer=False)

export("SM_LB_Weld_SkidLiftTransfer_v001", "WeldShop/SkidLiftTransfer_v001")
preview("SM_LB_Weld_SkidLiftTransfer_v001", "WeldShop/SkidLiftTransfer_v001")
