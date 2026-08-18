"""Paint shop power-and-free carrier: the hanger that dips a body in ED.

Recognised by its twin trolleys on the enclosed track, the load beam between
them, the four drop arms curling under into sill saddles, and the drain
holes story: the body sits nose-down slightly so the shell reads mid-dip
when placed over a tank. Floor pivot, geometry at height (track at 5.2 m so
the hanger clears a 3 m tank wall with a body).
"""
import math
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, STEEL, WARMWHITE, box, cyl, export,
                          preview, reset)

reset()

RAIL_Z = 5.2

# Twin trolleys with side rollers, and the pusher dog between them.
for tx in (-1.6, 1.6):
    box("TrolleyBody", (0.5, 0.30, 0.22), (tx, 0, RAIL_Z), CHARCOAL)
    for wx in (-0.16, 0.16):
        for sy in (-0.20, 0.20):
            cyl("TrolleyWheel", 0.08, 0.05, (tx + wx, sy, RAIL_Z + 0.06),
                STEEL, axis="Y", verts=14)
box("PusherDog", (0.24, 0.12, 0.26), (0, 0, RAIL_Z - 0.05), STEEL)

# Load beam and the four drop arms with sill saddles.
box("LoadBeam", (4.0, 0.16, 0.20), (0, 0, RAIL_Z - 0.28), GREEN)
for tx in (-1.6, 1.6):
    box("BeamLug", (0.22, 0.20, 0.18), (tx, 0, RAIL_Z - 0.12), CHARCOAL)
for dx in (-1.45, 1.45):
    for sy in (-0.85, 0.85):
        box("DropArm", (0.10, 0.10, 1.7), (dx, sy, RAIL_Z - 1.20), GREEN)
        box("ArmFoot", (0.55, 0.10, 0.10), (dx - 0.22 * (1 if dx > 0 else -1),
            sy, RAIL_Z - 2.08), GREEN)
        box("SillSaddle", (0.24, 0.14, 0.07), (dx - 0.42 * (1 if dx > 0
            else -1), sy, RAIL_Z - 2.00), STEEL)
    # Cross spreader between the two arms of each pair.
    box("Spreader", (0.10, 1.70, 0.10), (dx, 0, RAIL_Z - 0.55), CHARCOAL)
for sy in (-0.85, 0.85):
    box("StabiliserBar", (2.9, 0.06, 0.08), (0, sy, RAIL_Z - 1.85), CHARCOAL)

# Earthing strap and carrier ID plate - ED needs the shell earthed.
cyl("EarthStrap", 0.02, 1.5, (0.4, 0, RAIL_Z - 1.0), STEEL, verts=8)
box("IDPlate", (0.02, 0.14, 0.20), (1.51, -0.85, RAIL_Z - 0.9),
    WARMWHITE, chamfer=False)
box("CodeFlag", (0.18, 0.03, 0.12), (1.6, 0.17, RAIL_Z + 0.13), WARMWHITE,
    chamfer=False)

export("SM_LB_Paint_PFCarrier_v001", "PaintShop/PFCarrier_v001")
preview("SM_LB_Paint_PFCarrier_v001", "PaintShop/PFCarrier_v001")
