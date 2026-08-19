"""Weld overhead drop lift: the portal lift dropping bodies to floor level.

Recognised by the two fabricated columns under a crowned top beam, the
hoist house with its cable drum, the twin guide rails with the cradle
carriage riding them on lift chains, and the counterweight on the rear
of one column.
"""
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, STEEL, WARMWHITE, box, column, cyl,
                          export, preview, reset)

reset()

for cx in (-1.6, 1.6):
    column("Mast", (cx, 0, 0), 4.8, GREEN, width=0.3)
box("TopBeam", (3.9, 0.4, 0.32), (0, 0, 5.06), GREEN)
box("HoistHouse", (1.0, 0.6, 0.5), (0, 0, 5.47), CHARCOAL)
cyl("CableDrum", 0.14, 0.7, (0, 0, 5.32), STEEL, axis="X", verts=14)

# Guide rails and the cradle carriage on its lift chains.
for gx in (-0.55, 0.55):
    box("GuideRail", (0.09, 0.09, 4.8), (gx, 0.12, 2.5), STEEL)
    box("RailFoot", (0.16, 0.16, 0.1), (gx, 0.12, 0.05), CHARCOAL)
box("Carriage", (1.34, 0.26, 0.5), (0, 0.12, 2.5), CHARCOAL)
for ax in (-0.45, 0.45):
    box("CradleArm", (0.16, 0.95, 0.12), (ax, -0.35, 2.3), CHARCOAL)
    box("CradlePad", (0.2, 0.24, 0.06), (ax, -0.6, 2.39), GREEN)
    box("Chain", (0.035, 0.035, 2.47), (ax, 0.12, 3.98), STEEL,
        chamfer=False)

# Counterweight riding the face of the east mast.
for wy in (-0.14, 0.14):
    box("WeightGuide", (0.05, 0.05, 3.6), (1.42, wy, 1.95), STEEL,
        chamfer=False)
box("Counterweight", (0.22, 0.34, 0.9), (1.42, 0, 1.6), STEEL)
box("WeightChain", (0.03, 0.03, 2.85), (1.42, 0, 3.47), STEEL, chamfer=False)
box("Placard", (0.02, 0.3, 0.18), (-1.77, 0, 2.4), WARMWHITE, chamfer=False)

export("SM_LB_Weld_OverheadDropLift_v001", "WeldShop/OverheadDropLift_v001")
preview("SM_LB_Weld_OverheadDropLift_v001", "WeldShop/OverheadDropLift_v001")
