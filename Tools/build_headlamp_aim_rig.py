"""Assembly headlamp aim rig: the optical station at the end of the final line.

Recognised by the floor guide rails the car noses onto, the cross-slide
tower carrying two optical heads at headlamp height, the collimator boxes
with lens rings, and the console. Charcoal tower on a steel slide so the
optics read as precision kit, not another cabinet.
"""
import math
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, RED, STEEL, WARMWHITE, YELLOW, box,
                          cyl, export, preview, reset)

reset()

# Floor guides the car wheels nose onto, and the slide bed.
for sy in (-0.75, 0.75):
    box("WheelGuide", (2.2, 0.16, 0.07), (0.9, sy, 0.035), YELLOW,
        chamfer=False)
    box("GuideLead", (0.4, 0.16, 0.05), (2.1, sy, 0.025), YELLOW,
        rot=(0.0, -0.12, 0.0), chamfer=False)
box("SlideBed", (0.5, 2.6, 0.10), (-0.9, 0, 0.05), CHARCOAL)
box("SlideRail", (0.10, 2.5, 0.05), (-0.9, 0, 0.12), STEEL, chamfer=False)

# Cross-slide tower with two optical heads.
box("Carriage", (0.44, 0.50, 0.12), (-0.9, 0, 0.18), STEEL)
box("Tower", (0.30, 0.34, 1.30), (-0.9, 0, 0.89), GREEN)
box("TowerRib", (0.34, 0.06, 1.26), (-0.9, 0, 0.89), CHARCOAL)
for hz in (0.72, 1.16):
    box("OpticHead", (0.44, 0.40, 0.30), (-0.82, 0, hz), CHARCOAL)
    cyl("Lens", 0.10, 0.05, (-0.57, 0, hz), STEEL, axis="X", verts=20)
    cyl("LensGlass", 0.085, 0.015, (-0.53, 0, hz), WARMWHITE, axis="X",
        verts=20)
    box("HeadVernier", (0.06, 0.24, 0.04), (-0.86, 0, hz + 0.19), STEEL,
        chamfer=False)
cyl("TowerCrank", 0.06, 0.05, (-0.9, 0.20, 1.60), STEEL, axis="Y", verts=14)
box("LevelVial", (0.05, 0.16, 0.05), (-0.9, 0, 1.60), WARMWHITE,
    chamfer=False)

# Console and services.
box("Console", (0.40, 0.30, 1.00), (-0.9, 1.65, 0.50), GREEN)
box("ConsoleScreen", (0.02, 0.22, 0.16), (-0.69, 1.65, 0.85), WARMWHITE,
    chamfer=False)
cyl("ConsoleEStop", 0.04, 0.05, (-0.69, 1.55, 0.60), RED, axis="X")
cyl("Conduit", 0.02, 0.9, (-0.9, 1.30, 0.20), STEEL, axis="Y", verts=10)
box("IDPlate", (0.02, 0.18, 0.09), (-0.74, 0, 1.45), WARMWHITE, chamfer=False)

export("SM_LB_Assembly_HeadlampAimRig_v001", "AssemblyShop/HeadlampAim_v001")
preview("SM_LB_Assembly_HeadlampAimRig_v001", "AssemblyShop/HeadlampAim_v001")
