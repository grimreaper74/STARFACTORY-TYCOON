"""Press train electrical cabinet net: the Blender-native Meshy replacement.

Replaces SM_CA_Factory_Elect_net_MeshyMaster_v632, bound by all four
LBPressTrainAStation authorities. Plan dims 180 x 60 x 210 cm. A cabinet bank
is recognised by its repeated door bays with louvres and handles, the plinth,
and the cable tray dropping conduits into each bay from above.
"""
import math
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, RED, STEEL, WARMWHITE, YELLOW, box,
                          cyl, export, preview, reset)

reset()

box("Plinth", (1.80, 0.60, 0.10), (0, 0, 0.05), CHARCOAL)
for n, bx in enumerate((-0.60, 0.0, 0.60)):
    box("CabBody", (0.575, 0.55, 1.90), (bx, 0, 1.05), GREEN)
    box("CabDoor", (0.50, 0.02, 1.74), (bx, -0.285, 1.05), GREEN)
    box("DoorSeam", (0.015, 0.025, 1.74), (bx - 0.25, -0.285, 1.05), CHARCOAL,
        chamfer=False)
    cyl("Handle", 0.012, 0.16, (bx + 0.20, -0.30, 1.15), STEEL, verts=8)
    # Louvre stack low on each door.
    for v in range(5):
        box("Louvre", (0.34, 0.02, 0.025), (bx, -0.30, 0.42 + v * 0.06),
            CHARCOAL, chamfer=False)
    box("Label", (0.16, 0.015, 0.06), (bx, -0.30, 1.86), WARMWHITE,
        chamfer=False)
# Meters and an isolator distinguish the bays from one another.
for mx in (-0.10, 0.10):
    box("Meter", (0.12, 0.02, 0.12), (mx, -0.30, 1.55), WARMWHITE,
        chamfer=False)
cyl("Isolator", 0.045, 0.05, (-0.60, -0.31, 1.55), YELLOW, axis="Y")
cyl("EStop", 0.05, 0.05, (0.60, -0.31, 1.55), RED, axis="Y")
# Cable tray along the top with a conduit drop into each bay.
box("TopTray", (1.90, 0.30, 0.08), (0, 0.05, 2.14), STEEL)
for bx in (-0.60, 0.0, 0.60):
    cyl("TrayDrop", 0.030, 0.14, (bx, 0.05, 2.04), CHARCOAL, verts=12)
for gx in (-0.88, 0.88):
    box("GlandPlate", (0.02, 0.40, 0.50), (gx, 0.02, 0.55), CHARCOAL,
        chamfer=False)

export("SM_LB_ElectricalCabinetNet_v001", "PressShop/ElectricalCabinetNet_v001")
preview("SM_LB_ElectricalCabinetNet_v001", "PressShop/ElectricalCabinetNet_v001")
