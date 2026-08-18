"""Assembly sequenced wheel delivery carousel feeding station 17.

Recognised by the drive base, centre column with rotating spider arms, a
tyre stack on each arm with visible rims, the delivery chute at working
height, and the guard ring segments around the swing circle.
"""
import math
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, RED, STEEL, WARMWHITE, YELLOW, box,
                          cyl, export, preview, reset)

reset()


def wheel(x, y, z):
    cyl("Tyre", 0.33, 0.24, (x, y, z), CHARCOAL, axis="Z", verts=22)
    cyl("Rim", 0.19, 0.26, (x, y, z), STEEL, axis="Z", verts=18)
    cyl("Hub", 0.05, 0.28, (x, y, z), CHARCOAL, axis="Z", verts=10)


# Drive base and centre column.
cyl("Base", 0.65, 0.25, (0, 0, 0.125), CHARCOAL, verts=24)
box("DriveBox", (0.6, 0.5, 0.35), (0.8, 0, 0.18), GREEN)
cyl("DriveShaft", 0.06, 0.30, (0.45, 0, 0.18), STEEL, axis="X", verts=12)
cyl("Column", 0.14, 2.4, (0, 0, 1.45), GREEN, verts=16)
cyl("SlewRing", 0.30, 0.10, (0, 0, 0.30), STEEL, verts=24)

# Rotating spider: six arms, each with a two-tyre stack.
for n in range(6):
    a = n * math.pi / 3.0
    ax, ay = math.cos(a), math.sin(a)
    box("Arm", (1.35, 0.10, 0.10), (ax * 0.72, ay * 0.72, 1.30), GREEN,
        rot=(0.0, 0.0, a))
    cyl("Platter", 0.38, 0.04, (ax * 1.35, ay * 1.35, 1.38), STEEL, verts=20)
    wheel(ax * 1.35, ay * 1.35, 1.55)
    wheel(ax * 1.35, ay * 1.35, 1.82)
cyl("Crown", 0.18, 0.10, (0, 0, 2.70), CHARCOAL, verts=16)
cyl("Beacon", 0.04, 0.09, (0, 0, 2.80), RED)

# Delivery chute and guard ring segments.
box("Chute", (1.2, 0.75, 0.08), (1.9, 0, 1.05), STEEL, rot=(0.0, 0.22, 0.0))
for cy in (-0.36, 0.36):
    box("ChuteWall", (1.2, 0.04, 0.18), (1.9, cy, 1.16), GREEN,
        rot=(0.0, 0.22, 0.0), chamfer=False)
for n in range(4):
    a = math.pi * 0.55 + n * math.pi * 0.3
    box("GuardSeg", (0.9, 0.05, 1.0), (math.cos(a) * 2.05, math.sin(a) * 2.05,
        0.5), YELLOW, rot=(0.0, 0.0, a + math.pi * 0.5), chamfer=False)
box("IDPlate", (0.02, 0.2, 0.12), (0.51, 0, 0.35), WARMWHITE, chamfer=False)

export("SM_LB_Assembly_WheelCarousel_v001", "AssemblyShop/WheelCarousel_v001")
preview("SM_LB_Assembly_WheelCarousel_v001", "AssemblyShop/WheelCarousel_v001")
