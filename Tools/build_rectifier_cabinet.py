"""Paint ED rectifier cabinet: feeds DC to the tank anode rails.

Recognised by the heavy finned cabinet with its cooling stack, the paired
bus bars leaving the roof toward the tank, the isolator and meters, and
the warning chevrons on the plinth. Pairs with the dip tanks' bus boxes.
"""
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, STEEL, WARMWHITE, YELLOW, box, cyl,
                          export, preview, reset)

reset()

box("Plinth", (1.5, 0.9, 0.12), (0, 0, 0.06), CHARCOAL)
for n in range(6):
    box("Chevron", (0.18, 0.03, 0.10), (-0.62 + n * 0.25, -0.46, 0.07),
        YELLOW, rot=(0.0, 0.0, 0.6), chamfer=False)
box("Cabinet", (1.4, 0.8, 1.9), (0, 0, 1.07), GREEN)
for n in range(9):
    box("Fin", (0.02, 0.72, 1.5), (-0.55 + n * 0.14, 0.45, 1.05), CHARCOAL,
        chamfer=False)
box("CoolStack", (0.6, 0.5, 0.35), (0, 0.1, 2.2), CHARCOAL)
cyl("StackFan", 0.20, 0.10, (0, 0.1, 2.42), GREEN, verts=18)

# Bus bars leaving the roof, with standoff insulators.
for by in (-0.15, 0.15):
    box("BusBar", (0.9, 0.08, 0.04), (0.7, by, 2.1), STEEL, chamfer=False)
    cyl("BusInsulator", 0.05, 0.12, (0.45, by, 2.02), WARMWHITE, verts=10)
box("BusDrop", (0.04, 0.42, 0.6), (1.13, 0, 1.85), STEEL, chamfer=False)

# Door face: meters, isolator, warning plate.
for n, mx in enumerate((-0.35, -0.05)):
    cyl("Meter", 0.07, 0.03, (mx, -0.41, 1.6), WARMWHITE, axis="Y", verts=14)
cyl("Isolator", 0.05, 0.06, (0.4, -0.42, 1.6), YELLOW, axis="Y")
box("WarnPlate", (0.3, 0.02, 0.2), (0.25, -0.41, 1.1), WARMWHITE,
    chamfer=False)
box("DoorSeam", (0.015, 0.02, 1.7), (0, -0.41, 1.05), CHARCOAL,
    chamfer=False)
cyl("DoorHandle", 0.014, 0.16, (0.12, -0.43, 1.0), STEEL, verts=8)
box("IDPlate", (0.02, 0.2, 0.11), (-0.71, 0, 1.75), WARMWHITE, chamfer=False)

export("SM_LB_Paint_RectifierCabinet_v001", "PaintShop/Rectifier_v001")
preview("SM_LB_Paint_RectifierCabinet_v001", "PaintShop/Rectifier_v001")
