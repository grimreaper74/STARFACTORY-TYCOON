"""Weld shop marshalling rack: cantilever rack holding staged subassemblies.

The vendor shelving read as fencing, so this is the authored replacement:
heavy base, twin columns with three cantilever arm levels a side, staged
panel bundles on the arms, end stops and a load placard.
"""
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, STEEL, WARMWHITE, YELLOW, box, cyl,
                          export, preview, reset)

reset()

# Base rails and twin columns.
for sx in (-1.0, 1.0):
    box("BaseRail", (0.9, 2.20, 0.14), (sx, 0, 0.07), CHARCOAL)
    box("Column", (0.22, 0.26, 2.60), (sx, 0, 1.44), GREEN)
    box("ColumnCap", (0.28, 0.32, 0.06), (sx, 0, 2.77), CHARCOAL)
    for sy in (-1.0, 1.0):
        box("BaseGusset", (0.16, 0.35, 0.30), (sx, sy * 0.35, 0.30),
            CHARCOAL, rot=(sy * 0.5, 0.0, 0.0))
box("Spine", (2.0, 0.12, 0.16), (0, 0, 2.60), GREEN)
box("SpineLow", (2.0, 0.10, 0.12), (0, 0, 0.60), CHARCOAL)

# Three arm levels per side with staged panel bundles.
for lz in (0.95, 1.65, 2.35):
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            box("Arm", (0.09, 0.95, 0.10), (sx, sy * 0.55, lz), STEEL)
            box("ArmStop", (0.09, 0.05, 0.16), (sx, sy * 1.00, lz + 0.06),
                YELLOW, chamfer=False)
    # Panel bundle: a stack of thin pressed panels spanning the arms.
    for n in range(4):
        box("Bundle", (2.10, 1.55, 0.025), (0, 0, lz + 0.10 + n * 0.035),
            STEEL, chamfer=False)

box("Placard", (0.02, 0.40, 0.30), (-1.12, 0, 1.9), WARMWHITE, chamfer=False)

export("SM_LB_Weld_MarshallingRack_v001", "WeldShop/MarshallingRack_v001")
preview("SM_LB_Weld_MarshallingRack_v001", "WeldShop/MarshallingRack_v001")
