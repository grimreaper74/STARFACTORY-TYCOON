"""Press train operator HMI stand: the second and last Meshy replacement.

Replaces SM_CA_Factory_Opera_HMI_MeshyMaster_v632. Plan dims 70 x 45 x 160 cm.
A pedestal HMI is recognised by its angled console face on a single column,
the screen and button row, the e-stop, and the beacon that shows train state
to the aisle in a lights-out shop.
"""
import math
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, RED, STEEL, WARMWHITE, YELLOW, box,
                          cyl, export, preview, reset)

reset()

box("BasePlate", (0.50, 0.42, 0.045), (0, 0, 0.022), CHARCOAL)
for bx in (-1.0, 1.0):
    for by in (-1.0, 1.0):
        cyl("BaseBolt", 0.016, 0.045, (bx * 0.20, by * 0.16, 0.055), STEEL,
            verts=8)
box("Column", (0.13, 0.11, 0.85), (0, 0.04, 0.47), GREEN)
box("ColumnTray", (0.05, 0.04, 0.70), (0, 0.11, 0.50), STEEL, chamfer=False)

# Console with an angled face carrying the screen and controls.
box("Console", (0.66, 0.34, 0.34), (0, 0, 1.05), GREEN,
    rot=(math.radians(18.0), 0.0, 0.0))
box("Screen", (0.50, 0.02, 0.20), (0, -0.191, 1.051), WARMWHITE,
    rot=(math.radians(18.0), 0.0, 0.0), chamfer=False)
for n in range(4):
    cyl("Button", 0.016, 0.025, (-0.18 + n * 0.09, -0.185, 0.955), CHARCOAL,
        axis="Y", verts=10)
cyl("EStop", 0.042, 0.05, (0.24, -0.19, 0.96), RED, axis="Y")
box("Keyshelf", (0.55, 0.16, 0.03), (0, -0.24, 0.88), CHARCOAL)
for hx in (-0.34, 0.34):
    cyl("GrabHandle", 0.014, 0.30, (hx, -0.10, 1.02), STEEL, verts=10)

# Beacon mast showing the train state to the aisle.
cyl("BeaconMast", 0.015, 0.28, (0.22, 0.08, 1.36), STEEL, verts=10)
cyl("BeaconLamp", 0.038, 0.09, (0.22, 0.08, 1.55), RED)
cyl("BeaconCap", 0.040, 0.02, (0.22, 0.08, 1.60), CHARCOAL)
cyl("Conduit", 0.020, 0.80, (0, 0.10, 0.45), STEEL, verts=10)

export("SM_LB_OperatorHMIStand_v001", "PressShop/OperatorHMIStand_v001")
preview("SM_LB_OperatorHMIStand_v001", "PressShop/OperatorHMIStand_v001")
