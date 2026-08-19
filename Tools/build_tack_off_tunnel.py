"""Paint tack-off tunnel: the ionised blow-off module before base coat.

Recognised by the open-ended tunnel with portal frames, the side glazing
band, the roof plenum carrying three filter housings, and the angled
air-knife bars visible through the openings.
"""
import math
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, STEEL, WARMWHITE, box, cyl, export,
                          preview, reset)

reset()

for ry in (-1.0, 1.0):
    box("FloorRail", (6.0, 0.15, 0.1), (0, ry, 0.05), CHARCOAL)
for sy in (-1.17, 1.17):
    box("SideWall", (6.0, 0.06, 2.2), (0, sy, 1.2), GREEN)
    box("Glazing", (5.4, 0.03, 0.5), (0, sy * 1.02, 1.75), STEEL,
        chamfer=False)
box("Roof", (6.0, 2.46, 0.08), (0, 0, 2.34), GREEN)

# Portal frames at each open end.
for px in (-3.0, 3.0):
    for jy in (-1.2, 1.2):
        box("Jamb", (0.14, 0.14, 2.5), (px, jy, 1.25), CHARCOAL)
    box("Header", (0.14, 2.54, 0.22), (px, 0, 2.5), CHARCOAL)

# Roof plenum with filter housings.
box("Plenum", (5.4, 1.8, 0.5), (0, 0, 2.63), GREEN)
for n, fx in enumerate((-1.8, 0.0, 1.8)):
    box("FilterBox", (0.9, 1.2, 0.4), (fx, 0, 3.08), CHARCOAL)
    cyl("FilterStub", 0.1, 0.3, (fx, 0, 3.4), STEEL, verts=10)

# Angled air-knife bars across the body path.
for kx, kz in ((-1.5, 1.3), (1.5, 1.8)):
    box("AirKnife", (0.12, 2.3, 0.12), (kx, 0, kz), STEEL,
        rot=(0.0, math.radians(20.0), 0.0), chamfer=False)

box("Door", (0.7, 0.05, 1.3), (-2.2, -1.19, 0.85), GREEN)
box("DoorHandle", (0.05, 0.06, 0.16), (-1.95, -1.22, 0.85), STEEL)
box("Placard", (0.36, 0.02, 0.2), (0.5, -1.21, 1.3), WARMWHITE,
    chamfer=False)

export("SM_LB_Paint_TackOffTunnel_v001", "PaintShop/TackOffTunnel_v001")
preview("SM_LB_Paint_TackOffTunnel_v001", "PaintShop/TackOffTunnel_v001")
