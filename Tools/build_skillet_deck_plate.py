"""Assembly skillet deck plate: one 2 m module of the moving floor.

The trim and final lines ride on skillet conveyor - floor plates moving at
walking pace. One module is recognised by its anti-slip tread strips, the
marked leading edge, the side skirts hiding the chain bed, and the guide
rollers underneath. It repeats ~150 times, so restraint beats ornament.
"""
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, STEEL, YELLOW, box, cyl, export,
                          preview, reset)

reset()

# Deck plate with tread strips and marked edges.
box("Deck", (1.96, 1.76, 0.06), (0, 0, 0.35), GREEN)
for n in range(7):
    box("Tread", (0.14, 1.60, 0.015), (-0.78 + n * 0.26, 0, 0.385), CHARCOAL,
        chamfer=False)
for ex in (-0.97, 0.97):
    box("EdgeMark", (0.03, 1.76, 0.02), (ex, 0, 0.375), YELLOW, chamfer=False)

# Under-frame: rails, cross ribs and side skirts down to the slab.
for sy in (-0.80, 0.80):
    box("FrameRail", (1.90, 0.10, 0.14), (0, sy, 0.25), CHARCOAL)
    box("Skirt", (1.96, 0.03, 0.30), (0, sy * 1.09, 0.17), CHARCOAL,
        chamfer=False)
for rx in (-0.70, 0.0, 0.70):
    box("CrossRib", (0.08, 1.60, 0.10), (rx, 0, 0.22), CHARCOAL, chamfer=False)

# Guide rollers running in the floor channel.
for rx in (-0.75, 0.75):
    for sy in (-0.55, 0.55):
        cyl("Roller", 0.06, 0.08, (rx, sy, 0.08), STEEL, axis="Y", verts=14)
box("ChainBar", (1.90, 0.08, 0.06), (0, 0, 0.07), STEEL)

export("SM_LB_Conveyor_SkilletDeckPlate_v001", "AssemblyShop/SkilletDeckPlate_v001")
preview("SM_LB_Conveyor_SkilletDeckPlate_v001", "AssemblyShop/SkilletDeckPlate_v001")
