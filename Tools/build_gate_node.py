"""Site gate node: the automated main-gate control for a lights-out plant.

No manned gatehouse - recognised by the equipment cabin, the sensor
gantry spanning the roadway with camera housings and a status lamp, and
the two barrier booms (safety-yellow, a functional marking) on their
pivot posts.
"""
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, STEEL, WARMWHITE, YELLOW, box, cyl,
                          export, preview, reset)

reset()

# Equipment cabin beside the roadway.
box("CabinBase", (3.2, 2.2, 0.15), (-5.5, 0, 0.08), CHARCOAL)
box("Cabin", (3.0, 2.0, 2.4), (-5.5, 0, 1.35), GREEN)
box("CabinRoof", (3.15, 2.15, 0.1), (-5.5, 0, 2.6), CHARCOAL)
box("CabinDoor", (0.05, 0.9, 1.9), (-4.02, -0.3, 1.1), GREEN)
box("DoorHandle", (0.06, 0.06, 0.2), (-4.0, -0.7, 1.1), STEEL)
box("CabinLouvre", (0.05, 0.8, 0.6), (-6.98, 0, 1.7), STEEL, chamfer=False)
box("IDPlate", (0.02, 0.5, 0.25), (-4.0, 0.4, 1.8), WARMWHITE,
    chamfer=False)

# Sensor gantry spanning the 24 m roadway.
for gy in (-12.5, 12.5):
    box("GantryPost", (0.25, 0.25, 5.6), (0, gy, 2.8), GREEN)
    box("GantryFoot", (0.5, 0.5, 0.08), (0, gy, 0.04), CHARCOAL)
box("GantryBeam", (0.3, 25.6, 0.4), (0, 0, 5.5), GREEN)
for cy in (-8.0, -2.5, 2.5, 8.0):
    box("Camera", (0.25, 0.3, 0.25), (-0.2, cy, 5.15), CHARCOAL)
    cyl("Lens", 0.06, 0.1, (-0.36, cy, 5.15), STEEL, axis="X", verts=10)
cyl("StatusLamp", 0.09, 0.25, (0, 0, 5.82), ("MAT_StatusGreen",
    (0.05, 0.5, 0.15, 1.0)), verts=12)

# Barrier booms on pivot posts, one per carriageway.
for by, yaw in ((-6.2, 1), (6.2, -1)):
    box("BarrierPost", (0.35, 0.35, 1.1), (0, by, 0.55), GREEN)
    box("BarrierHead", (0.5, 0.4, 0.45), (0, by, 1.3), CHARCOAL)
    box("Boom", (0.12, 5.6, 0.18), (0, by + yaw * 3.0, 1.25), YELLOW)
    box("BoomTip", (0.13, 0.5, 0.19), (0, by + yaw * 5.6, 1.25), CHARCOAL)

export("SM_LB_Site_GateNode_v001", "Site/GateNode_v001")
preview("SM_LB_Site_GateNode_v001", "Site/GateNode_v001")
