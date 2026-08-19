"""Paint AHU module: the air handling unit feeding the booth plenums.

Recognised by the long panelled casing with lifted corner feet, the intake
louvre bank on one end, the bulged fan section with its access door and
viewport, the discharge duct stub on the roof, and the gauge panel.
"""
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, STEEL, WARMWHITE, box, cyl, export,
                          preview, reset)

reset()

# Casing on corner feet with panel seams.
for fx in (-2.0, 0.0, 2.0):
    for fy in (-0.75, 0.75):
        box("Foot", (0.14, 0.14, 0.25), (fx, fy, 0.125), CHARCOAL)
box("Casing", (4.4, 1.7, 1.9), (0, 0, 1.20), GREEN)
for n in range(4):
    box("SeamV", (0.05, 1.74, 1.9), (-1.5 + n * 1.0, 0, 1.20), CHARCOAL,
        chamfer=False)
box("SeamH", (4.4, 1.74, 0.05), (0, 0, 1.20), CHARCOAL, chamfer=False)

# Intake louvre bank and the discharge stub.
for n in range(6):
    box("Louvre", (0.02, 1.5, 0.16), (-2.21, 0, 0.55 + n * 0.26), STEEL,
        rot=(0.0, 0.5, 0.0), chamfer=False)
box("DischargeStub", (0.8, 0.8, 0.5), (1.4, 0, 2.4), GREEN)
box("StubFlange", (0.9, 0.9, 0.06), (1.4, 0, 2.68), CHARCOAL, chamfer=False)

# Fan section: access door with viewport, and the gauge panel.
box("FanDoor", (0.7, 0.03, 1.2), (1.0, -0.87, 1.1), GREEN)
box("DoorFrame", (0.8, 0.02, 1.3), (1.0, -0.865, 1.1), CHARCOAL,
    chamfer=False)
cyl("Viewport", 0.09, 0.03, (1.0, -0.89, 1.5), WARMWHITE, axis="Y", verts=14)
cyl("DoorHandle", 0.013, 0.14, (0.72, -0.9, 1.0), STEEL, verts=8)
box("GaugePanel", (0.45, 0.02, 0.3), (-0.6, -0.86, 1.5), CHARCOAL,
    chamfer=False)
for n in range(3):
    cyl("Gauge", 0.05, 0.02, (-0.72 + n * 0.13, -0.875, 1.5), WARMWHITE,
        axis="Y", verts=12)
box("IDPlate", (0.24, 0.02, 0.12), (-1.6, -0.86, 1.7), WARMWHITE,
    chamfer=False)

export("SM_LB_Paint_AHU_Module_v001", "PaintShop/AHUModule_v001")
preview("SM_LB_Paint_AHU_Module_v001", "PaintShop/AHUModule_v001")
