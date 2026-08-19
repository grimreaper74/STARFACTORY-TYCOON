"""Paint oven burner house: the fired heater set feeding the oven band.

Recognised by the seamed cabinet with its supply and return ducts turning
south toward the oven, the snail blower with motor on the south face, the
gas train with handwheel valves along the west side, and the intake
louvre on the east face.
"""
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, STEEL, WARMWHITE, box, cyl, export,
                          preview, reset)

reset()

box("Plinth", (3.2, 2.0, 0.12), (0, 0, 0.06), CHARCOAL)
box("Body", (3.0, 1.8, 2.2), (0, 0, 1.22), GREEN)
for sx in (-1.0, 0.0, 1.0):
    box("Seam", (0.06, 1.84, 2.2), (sx, 0, 1.22), CHARCOAL, chamfer=False)
box("BodyCap", (3.06, 1.86, 0.08), (0, 0, 2.36), CHARCOAL)

# Supply and return ducts rising and turning south toward the oven.
for dx, dn in ((-0.7, "Supply"), (0.7, "Return")):
    box(dn + "Riser", (0.7, 0.6, 0.8), (dx, 0, 2.8), GREEN)
    box(dn + "Run", (0.6, 1.4, 0.55), (dx, -0.9, 2.9), GREEN)
    box(dn + "Flange", (0.66, 0.08, 0.61), (dx, -1.62, 2.9), CHARCOAL,
        chamfer=False)

# Snail blower with motor on the south face.
cyl("BlowerCase", 0.42, 0.38, (0.0, -1.05, 1.3), CHARCOAL, axis="Y",
    verts=20)
cyl("BlowerInlet", 0.2, 0.16, (0.0, -1.3, 1.3), STEEL, axis="Y", verts=14)
cyl("Motor", 0.17, 0.45, (0.55, -1.12, 1.3), STEEL, axis="Y", verts=14)
box("MotorBase", (0.4, 0.44, 0.08), (0.55, -1.1, 1.1), CHARCOAL)

# Gas train with handwheel valves along the west side, clipped to the face.
cyl("GasMain", 0.06, 1.9, (-1.62, 0, 0.9), STEEL, axis="Y", verts=12)
for cy in (-0.35, 0.15):
    box("PipeClip", (0.16, 0.08, 0.08), (-1.56, cy, 0.9), CHARCOAL,
        chamfer=False)
for n, vy in enumerate((-0.6, -0.1, 0.4)):
    box("ValveBody", (0.14, 0.16, 0.14), (-1.62, vy, 0.9), GREEN)
    cyl("ValveWheel", 0.09, 0.04, (-1.62, vy, 1.06), CHARCOAL, verts=12)
cyl("GasDrop", 0.05, 0.9, (-1.62, 0.75, 1.35), STEEL, verts=10)

# Intake louvre on the east face.
box("LouvreFrame", (0.06, 1.0, 1.1), (1.53, 0, 1.35), CHARCOAL,
    chamfer=False)
for n in range(5):
    box("Slat", (0.05, 0.9, 0.1), (1.55, 0, 0.95 + n * 0.2), STEEL,
        rot=(0.5, 0.0, 0.0), chamfer=False)

box("Door", (0.8, 0.05, 1.4), (0.9, -0.93, 0.95), GREEN)
box("DoorHandle", (0.05, 0.06, 0.18), (0.6, -0.96, 0.95), STEEL)
box("Placard", (0.4, 0.02, 0.22), (-0.9, -0.93, 1.7), WARMWHITE,
    chamfer=False)
cyl("Flue", 0.14, 0.6, (1.1, 0.5, 2.7), STEEL, verts=12)

export("SM_LB_Paint_OvenBurnerHouse_v001", "PaintShop/OvenBurnerHouse_v001")
preview("SM_LB_Paint_OvenBurnerHouse_v001", "PaintShop/OvenBurnerHouse_v001")
