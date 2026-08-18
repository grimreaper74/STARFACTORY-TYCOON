"""Assembly rolls dyno and brake test bed: the flush floor rollers at test.

Recognised by the flush bed plate with two recessed roller pairs, the yellow
surround marking the pit edge, wheel chocks and tie-down anchors, and the
operator console with its result display. Mostly floor-flush, so the reads
come from the surround and the rollers themselves.
"""
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, RED, STEEL, WARMWHITE, YELLOW, box,
                          cyl, export, preview, reset)

reset()

# Bed plate with the yellow pit surround.
box("BedPlate", (7.0, 4.0, 0.12), (0, 0, 0.06), CHARCOAL)
for sy in (-1.98, 1.98):
    box("SurroundY", (7.0, 0.06, 0.14), (0, sy, 0.07), YELLOW, chamfer=False)
for sx in (-3.48, 3.48):
    box("SurroundX", (0.06, 4.0, 0.14), (sx, 0, 0.07), YELLOW, chamfer=False)

# Two roller pairs per axle track, recessed in dark pits.
for px in (-1.1, 1.1):
    for sy in (-0.95, 0.95):
        box("Pit", (0.95, 1.15, 0.02), (px, sy, 0.125), CHARCOAL,
            chamfer=False)
        for rx in (-0.22, 0.22):
            cyl("Roller", 0.16, 1.00, (px + rx, sy, 0.05), STEEL, axis="Y",
                verts=20)
        box("PitGrate", (0.06, 1.10, 0.02), (px, sy, 0.135), STEEL,
            chamfer=False)

# Centre guide plates, chocks and tie-down anchors.
box("CentreGuide", (5.6, 0.14, 0.05), (0, 0, 0.145), STEEL)
for cx in (-2.6, 2.6):
    for sy in (-0.95, 0.95):
        box("Chock", (0.24, 0.30, 0.14), (cx, sy, 0.19), YELLOW)
for ax in (-3.0, 0.0, 3.0):
    cyl("TieDown", 0.06, 0.03, (ax, -1.7, 0.135), STEEL, verts=12)

# Operator console with result display and beacon.
box("Console", (0.50, 0.36, 1.30), (0, 2.45, 0.65), GREEN)
box("ConsoleScreen", (0.30, 0.02, 0.22), (0, 2.26, 1.05), WARMWHITE,
    chamfer=False)
cyl("ConsoleEStop", 0.045, 0.05, (0.16, 2.25, 0.75), RED, axis="Y")
cyl("Beacon", 0.04, 0.09, (0, 2.45, 1.40), RED)
box("Bollard1", (0.10, 0.10, 0.60), (-3.3, 2.1, 0.30), YELLOW)
box("Bollard2", (0.10, 0.10, 0.60), (3.3, 2.1, 0.30), YELLOW)

export("SM_LB_Assembly_RollsDynoBrakeTestBed_v001", "AssemblyShop/RollsDyno_v001")
preview("SM_LB_Assembly_RollsDynoBrakeTestBed_v001", "AssemblyShop/RollsDyno_v001")
