"""Weld shop respot fixture: locates the framed body while robots re-weld.

Recognised by its low bed frame with four rest towers carrying NC blocks,
the swing clamps at each tower, the datum pin pair, and the valve island
with its dressed air runs. Sits between the framing gate and the respot
robots.
"""
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, RED, STEEL, WARMWHITE, YELLOW, box,
                          cyl, export, preview, reset)

reset()

# Bed frame on levelling feet.
for sy in (-0.75, 0.75):
    box("BedRail", (3.60, 0.18, 0.22), (0, sy, 0.28), GREEN)
for cx in (-1.5, 0.0, 1.5):
    box("BedCross", (0.16, 1.60, 0.18), (cx, 0, 0.26), CHARCOAL)
for fx in (-1.6, 1.6):
    for fy in (-0.75, 0.75):
        cyl("Foot", 0.05, 0.14, (fx, fy, 0.07), STEEL, verts=10)
        box("FootPlate", (0.16, 0.16, 0.03), (fx, fy, 0.015), CHARCOAL,
            chamfer=False)

# Four rest towers with NC blocks and swing clamps.
for tx in (-1.35, 1.35):
    for ty in (-0.62, 0.62):
        box("Tower", (0.16, 0.16, 0.55), (tx, ty, 0.66), GREEN)
        box("TowerRib", (0.20, 0.05, 0.40), (tx, ty, 0.58), CHARCOAL)
        box("NCBlock", (0.20, 0.14, 0.10), (tx, ty, 0.98), STEEL)
        box("RestPad", (0.14, 0.10, 0.03), (tx, ty, 1.045), CHARCOAL,
            chamfer=False)
        # Swing clamp beside each tower.
        cyl("ClampCyl", 0.045, 0.20, (tx, ty + (0.18 if ty > 0 else -0.18),
            0.80), CHARCOAL, verts=12)
        box("ClampArm", (0.06, 0.20, 0.05), (tx, ty + (0.12 if ty > 0
            else -0.12), 0.99), STEEL)

# Datum pins at the centreline and the valve island.
for px in (-0.6, 0.6):
    cyl("DatumPin", 0.035, 0.30, (px, 0, 0.95), STEEL, verts=10)
    cyl("DatumBoss", 0.06, 0.10, (px, 0, 0.78), CHARCOAL, verts=12)
box("ValveIsland", (0.45, 0.20, 0.18), (0, -0.95, 0.42), GREEN)
for n in range(4):
    cyl("ValveCoil", 0.025, 0.08, (-0.14 + n * 0.09, -0.95, 0.55), CHARCOAL,
        verts=8)
cyl("AirMain", 0.022, 3.0, (0, -0.92, 0.30), STEEL, axis="X", verts=10)
box("JBox", (0.14, 0.10, 0.16), (1.55, -0.9, 0.45), GREEN)
box("IDPlate", (0.02, 0.18, 0.10), (-1.81, -0.75, 0.32), WARMWHITE, chamfer=False)

export("SM_LB_Weld_RespotFixture_v001", "WeldShop/RespotFixture_v001")
preview("SM_LB_Weld_RespotFixture_v001", "WeldShop/RespotFixture_v001")
