"""Paint mix room skid: agitated mix vessels feeding the booth robots.

Recognised by the two tall agitated vessels with drive motors on their
lids, the circulating pump pair, the shared manifold with valve wheels,
level gauges, and the control cabinet on the skid end.
"""
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, RED, STEEL, WARMWHITE, YELLOW, box,
                          cyl, export, preview, reset)

reset()

box("Skid", (2.4, 1.2, 0.12), (0, 0, 0.06), CHARCOAL)
for sy in (-0.56, 0.56):
    box("BundRail", (2.4, 0.05, 0.18), (0, sy, 0.16), YELLOW, chamfer=False)

# Two agitated vessels with lids, drives and level gauges.
for vx in (-0.6, 0.6):
    cyl("Vessel", 0.42, 1.6, (vx, 0.15, 0.92), GREEN, verts=22)
    cyl("VesselLid", 0.45, 0.08, (vx, 0.15, 1.76), CHARCOAL, verts=22)
    cyl("AgitatorDrive", 0.14, 0.30, (vx, 0.15, 1.95), CHARCOAL, verts=14)
    cyl("DriveMotor", 0.09, 0.22, (vx, 0.15, 2.20), GREEN, verts=12)
    box("LevelGauge", (0.04, 0.05, 1.2), (vx + 0.45, -0.02, 0.95), WARMWHITE,
        chamfer=False)
    for gz in (0.5, 0.95, 1.4):
        box("GaugeClamp", (0.06, 0.07, 0.04), (vx + 0.45, -0.02, gz),
            CHARCOAL, chamfer=False)
    cyl("Outlet", 0.035, 0.3, (vx, -0.28, 0.3), STEEL, axis="Y", verts=10)

# Circulating pumps and the shared manifold with valve wheels.
for px in (-0.35, 0.35):
    cyl("CircPump", 0.13, 0.3, (px, -0.48, 0.40), GREEN, axis="X", verts=14)
    box("PumpBase", (0.32, 0.18, 0.10), (px, -0.48, 0.20), CHARCOAL)
cyl("Manifold", 0.045, 2.0, (0, -0.52, 0.68), STEEL, axis="X", verts=12)
for n, mx in enumerate((-0.8, -0.27, 0.27, 0.8)):
    cyl("Valve", 0.08, 0.04, (mx, -0.52, 0.80), YELLOW, axis="Z", verts=12)
cyl("SupplyRiser", 0.04, 1.6, (1.05, -0.4, 1.0), STEEL, verts=10)

box("Cabinet", (0.4, 0.3, 0.9), (-1.0, -0.35, 0.57), GREEN)
box("CabDoor", (0.02, 0.26, 0.78), (-1.21, -0.35, 0.57), CHARCOAL,
    chamfer=False)
cyl("CabEStop", 0.035, 0.04, (-1.22, -0.42, 0.8), RED, axis="X")
box("IDPlate", (0.02, 0.2, 0.11), (-1.19, 0.2, 0.3), WARMWHITE,
    chamfer=False)

export("SM_LB_Paint_MixRoomSkid_v001", "PaintShop/MixRoomSkid_v001")
preview("SM_LB_Paint_MixRoomSkid_v001", "PaintShop/MixRoomSkid_v001")
