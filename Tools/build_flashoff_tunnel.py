"""Paint flash-off tunnel: the open-sided vent section before the oven.

Lighter than the oven by design: portal frames with slatted side walls for
airflow, twin roof extract cowls, warmwhite heat-lamp strips inside the
roof, and the carrier slot along the crown. 6 m module that chains.
"""
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, STEEL, WARMWHITE, box, cyl, export,
                          preview, reset)

reset()

L, W, H = 6.0, 4.2, 4.4

# Portal frames and the slatted side walls.
for px in (-2.9, 0.0, 2.9):
    for sy in (-W * 0.5, W * 0.5):
        box("PortalLeg", (0.20, 0.20, H - 0.3), (px, sy, (H - 0.3) * 0.5),
            CHARCOAL)
    box("PortalHead", (0.20, W + 0.15, 0.26), (px, 0, H - 0.15), CHARCOAL)
for sy in (-W * 0.5, W * 0.5):
    for n in range(8):
        box("Slat", (L, 0.05, 0.28), (0, sy * 1.01, 0.7 + n * 0.42), GREEN,
            rot=(0.35 * (1 if sy > 0 else -1), 0.0, 0.0), chamfer=False)
    box("SlatSill", (L, 0.10, 0.14), (0, sy, 0.35), GREEN)

# Roof deck with the carrier slot and extract cowls.
box("Roof", (L, W + 0.1, 0.10), (0, 0, H + 0.05), GREEN)
box("RoofSlot", (L, 0.30, 0.12), (0, 0, H + 0.12), CHARCOAL, chamfer=False)
for fx in (-1.5, 1.5):
    box("CowlBase", (0.9, 0.9, 0.20), (fx, 0.9, H + 0.18), CHARCOAL)
    cyl("Cowl", 0.34, 0.5, (fx, 0.9, H + 0.5), GREEN, verts=18)
    cyl("CowlCap", 0.40, 0.07, (fx, 0.9, H + 0.78), CHARCOAL, verts=18)

# Heat lamp strips inside the roof, visible through the open sides.
for ly in (-1.0, 0.0, 1.0):
    box("LampStrip", (L - 0.8, 0.14, 0.05), (0, ly, H - 0.30), WARMWHITE,
        chamfer=False)
    box("LampHousing", (L - 0.7, 0.20, 0.05), (0, ly, H - 0.24), CHARCOAL,
        chamfer=False)
box("IDPlate", (0.02, 0.3, 0.16), (-2.99, -1.2, 1.9), WARMWHITE,
    chamfer=False)

export("SM_LB_Paint_FlashOffTunnel_v001", "PaintShop/FlashOff_v001")
preview("SM_LB_Paint_FlashOffTunnel_v001", "PaintShop/FlashOff_v001")
