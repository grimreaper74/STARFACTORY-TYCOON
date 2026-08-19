"""Weld closure fixture for doors: the geo jig that holds a door shell.

Recognised by the pedestal-mounted tombstone plate, the proud door-outline
frame with its waist bar, the ring of toggle clamps, and the two shot
pins. Clamp faces point south so the detail reads from the aisle.
"""
import math
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, STEEL, WARMWHITE, box, cyl, export,
                          preview, reset)

reset()

box("BasePlate", (1.5, 1.1, 0.12), (0, 0, 0.06), CHARCOAL)
for fx in (-0.6, 0.6):
    for fy in (-0.4, 0.4):
        cyl("Foot", 0.04, 0.06, (fx, fy, 0.02), STEEL, verts=10)
box("Pedestal", (0.55, 0.42, 0.5), (0, 0.12, 0.37), GREEN)
box("PedestalCap", (0.65, 0.5, 0.05), (0, 0.12, 0.64), CHARCOAL)
box("Tombstone", (1.24, 0.10, 1.3), (0, 0.2, 1.31), GREEN)
box("TombstoneRib", (0.08, 0.16, 1.1), (0, 0.31, 1.28), CHARCOAL)

# Door-outline frame proud of the south face, with the waist bar.
FZ_TOP, FZ_BOT, FY = 1.72, 0.92, 0.11
box("FrameTop", (1.04, 0.05, 0.05), (0, FY, FZ_TOP), STEEL)
box("FrameBottom", (1.04, 0.05, 0.05), (0, FY, FZ_BOT), STEEL)
for vx in (-0.5, 0.5):
    box("FrameSide", (0.05, 0.05, 0.85), (vx, FY, 1.32), STEEL)
box("WaistBar", (1.0, 0.04, 0.04), (0, FY, 1.3), STEEL)

# Toggle clamps around the frame; levers angled back over the plate.
CLAMPS = [(-0.35, FZ_TOP + 0.06), (0.0, FZ_TOP + 0.06), (0.35, FZ_TOP + 0.06),
          (-0.58, 1.1), (0.58, 1.1), (0.0, FZ_BOT - 0.08)]
for cx, cz in CLAMPS:
    box("ClampBase", (0.09, 0.07, 0.07), (cx, FY, cz), STEEL)
    box("ClampLever", (0.03, 0.14, 0.03), (cx, FY + 0.05, cz + 0.07),
        CHARCOAL, rot=(math.radians(35.0), 0.0, 0.0), chamfer=False)

# Shot pins through the plate at the hinge datums.
for px in (-0.3, 0.3):
    cyl("ShotPin", 0.03, 0.18, (px, 0.09, 0.98), STEEL, axis="Y", verts=10)

box("JBox", (0.2, 0.12, 0.26), (0.45, 0.31, 0.9), GREEN)
cyl("Conduit", 0.02, 0.7, (0.45, 0.31, 0.45), STEEL, verts=8)
box("IDPlate", (0.26, 0.02, 0.14), (0, -0.1, 0.5), WARMWHITE, chamfer=False)

export("SM_LB_Weld_ClosureDoorFixture_v001", "WeldShop/ClosureDoorFixture_v001")
preview("SM_LB_Weld_ClosureDoorFixture_v001", "WeldShop/ClosureDoorFixture_v001")
