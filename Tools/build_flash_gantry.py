"""Assembly software flash gantry with OBD arm and server rack.

Recognised by the portal over the line, the articulated OBD service arm
hanging from its trolley with the connector head at door height, the
server rack cabinet with unit strips and status lights, and the antenna
mast for the over-the-air check.
"""
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, RED, STEEL, WARMWHITE, YELLOW, box,
                          column, cyl, export, preview, reset)

reset()

# Portal over the line.
for sy in (-1.7, 1.7):
    column("Post", (0, sy, 0), 3.4, GREEN, width=0.26)
box("Beam", (0.45, 3.8, 0.30), (0, 0, 3.65), GREEN)

# OBD service arm: trolley on the beam, articulated drop to connector head.
box("ArmTrolley", (0.35, 0.30, 0.14), (0, -0.5, 3.48), CHARCOAL)
cyl("ArmUpper", 0.045, 1.1, (0, -0.5, 2.85), STEEL, verts=12)
box("ArmElbow", (0.13, 0.13, 0.13), (0, -0.5, 2.28), CHARCOAL)
cyl("ArmLower", 0.035, 0.9, (0, -0.62, 1.85), STEEL, verts=10,
    axis="Z")
box("ConnectorHead", (0.14, 0.10, 0.22), (0, -0.62, 1.32), GREEN)
cyl("Cable", 0.018, 1.6, (0.08, -0.56, 2.4), CHARCOAL, verts=8)

# Server rack beside the +Y post with unit strips and status lights.
box("RackBase", (0.7, 0.5, 0.10), (0, 2.35, 0.05), CHARCOAL)
box("Rack", (0.62, 0.42, 1.90), (0, 2.35, 1.05), GREEN)
for n in range(7):
    box("RackUnit", (0.44, 0.02, 0.10), (0, 2.13, 0.35 + n * 0.24),
        CHARCOAL, chamfer=False)
    cyl("UnitLamp", 0.014, 0.02, (-0.16, 2.12, 0.38 + n * 0.24), WARMWHITE,
        axis="Y", verts=8)
box("RackVent", (0.40, 0.02, 0.14), (0, 2.13, 1.90), CHARCOAL,
    chamfer=False)
cyl("Antenna", 0.015, 0.9, (0, 2.35, 2.55), STEEL, verts=8)
cyl("AntennaTip", 0.03, 0.06, (0, 2.35, 3.02), CHARCOAL, verts=8)
cyl("RackConduit", 0.025, 1.2, (0, 2.58, 1.4), STEEL, verts=10,
    axis="Z")
cyl("Beacon", 0.04, 0.09, (0, 1.7, 3.86), RED)
box("IDPlate", (0.20, 0.02, 0.11), (0, 2.13, 2.05), WARMWHITE,
    chamfer=False)

export("SM_LB_Assembly_FlashGantry_v001", "AssemblyShop/FlashGantry_v001")
preview("SM_LB_Assembly_FlashGantry_v001", "AssemblyShop/FlashGantry_v001")
