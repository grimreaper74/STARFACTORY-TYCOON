"""Panel destack magazine - holds a stack of pressed panels, fans them with magnets so
they separate, and presents the top one for a robot to pick. Four feed the weld
receiving lane. Recognised by its corner guide masts, the fanned panel stack, the
magnet blocks on the flanks, and the light-curtain posts at the pick face.
"""
import math
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, RED, STEEL, WARMWHITE, YELLOW, box,
                          cyl, export, preview, reset, scissor)

reset()
W, D = 2.3, 1.8

# Base frame with skirt, and the scissor lift that raises the stack.
box("Base", (W, D, 0.18), (0, 0, 0.09), CHARCOAL)
box("Skirt", (W + 0.1, D + 0.1, 0.05), (0, 0, 0.025), YELLOW)
scissor("Lift", (0, 0, 0.42), 0.9, 0.4, CHARCOAL)
box("LiftDeck", (1.7, 1.2, 0.08), (0, 0, 0.66), STEEL)

# The panel stack, slightly fanned - each panel offset and tilted a touch.
for n in range(9):
    box("Panel", (1.6, 1.1, 0.02),
        (0.02 * (n % 3 - 1), 0.015 * (n % 2), 0.74 + n * 0.035),
        WARMWHITE if n % 2 else STEEL,
        rot=(0.0, math.radians(0.6 * (n % 3 - 1)), 0.0), chamfer=False)

# Corner guide masts: L-angles with adjuster handwheels.
for sx in (-1, 1):
    for sy in (-1, 1):
        x, y = sx * 0.88, sy * 0.62
        box("GuideA", (0.1, 0.03, 1.9), (x, y + sy * 0.015, 1.13), GREEN)
        box("GuideB", (0.03, 0.1, 1.9), (x + sx * 0.015, y, 1.13), GREEN)
        cyl("Adjuster", 0.045, 0.06, (x + sx * 0.12, y, 0.5), STEEL, axis="X",
            verts=12)

# Fanning magnet blocks on both flanks, finned, with junction boxes.
for sy in (-1, 1):
    for fx in (-0.45, 0.45):
        box("Magnet", (0.34, 0.12, 0.5), (fx, sy * 0.72, 1.05), GREEN)
        for n in range(4):
            box("MagFin", (0.36, 0.02, 0.09), (fx, sy * 0.72, 0.88 + n * 0.11),
                CHARCOAL, chamfer=False)
        box("MagJBox", (0.12, 0.08, 0.1), (fx, sy * 0.82, 1.38), CHARCOAL)
cyl("MagConduit", 0.02, 1.3, (0, 0.78, 0.6), STEEL, axis="X")

# Light-curtain posts at the pick face, with emitter strips.
for sy in (-1, 1):
    box("CurtainFoot", (0.2, 0.2, 0.04), (1.28, sy * 0.75, 0.02), CHARCOAL)
    box("CurtainPost", (0.08, 0.08, 1.7), (1.28, sy * 0.75, 0.89), YELLOW)
    box("CurtainStrip", (0.03, 0.02, 1.4), (1.24, sy * 0.75, 0.89), RED,
        chamfer=False)
    box("CurtainHead", (0.1, 0.1, 0.06), (1.28, sy * 0.75, 1.77), CHARCOAL)

# Controls on the rear flank.
box("Cabinet", (0.34, 0.24, 0.6), (-1.32, 0.4, 0.62), GREEN)
box("CabDoor", (0.02, 0.2, 0.5), (-1.5, 0.4, 0.63), CHARCOAL, chamfer=False)
cyl("EStop", 0.05, 0.06, (-1.5, 0.3, 0.85), RED, axis="X")
cyl("Beacon", 0.04, 0.12, (-1.32, 0.4, 1.0), YELLOW)

export("SM_LB_Weld_DestackMagazine_v001", "WeldShop/DestackMagazine_v001")
preview("SM_LB_Weld_DestackMagazine_v001", "WeldShop/DestackMagazine_v001")
