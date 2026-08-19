"""Paint sealer deck: the raised platform the sealer robots work from.

Recognised by its grated deck on legs with edge rails on the outer side,
two robot plinths with bolt rings, twin drum pump sets feeding the plinths,
and the kick plates. Robots mount on the plinths at placement.
"""
import math
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, STEEL, WARMWHITE, YELLOW, box, cyl,
                          export, preview, reset)

reset()

# Deck on legs with grating strips.
box("DeckFrame", (5.0, 2.0, 0.12), (0, 0, 0.56), GREEN)
for n in range(12):
    box("Grate", (0.38, 1.9, 0.02), (-2.3 + n * 0.42, 0, 0.635), STEEL,
        chamfer=False)
for lx in (-2.3, 0.0, 2.3):
    for ly in (-0.85, 0.85):
        box("Leg", (0.12, 0.12, 0.5), (lx, ly, 0.25), CHARCOAL)
box("KickPlate", (5.0, 0.03, 0.10), (0, 1.0, 0.68), YELLOW, chamfer=False)

# Edge rails on the outer side only - the line side stays open for reach.
for rz in (1.0, 1.35):
    box("Rail", (5.0, 0.05, 0.05), (0, 1.0, rz), STEEL, chamfer=False)
for rx in (-2.45, 0.0, 2.45):
    box("RailPost", (0.06, 0.06, 0.75), (rx, 1.0, 1.0), STEEL)

# Two robot plinths with bolt rings.
for px in (-1.3, 1.3):
    box("Plinth", (0.7, 0.7, 0.35), (px, -0.3, 0.79), CHARCOAL)
    for a in range(6):
        ang = a * math.pi / 3.0
        cyl("PlinthBolt", 0.02, 0.05, (px + 0.26 * math.cos(ang),
            -0.3 + 0.26 * math.sin(ang), 0.985), STEEL, verts=8)

# Drum pump sets behind the plinths.
for px in (-1.3, 1.3):
    cyl("Drum", 0.22, 0.7, (px, 0.55, 0.97), STEEL, verts=18)
    cyl("DrumPump", 0.06, 0.35, (px, 0.55, 1.45), CHARCOAL, verts=12)
    cyl("SealerHose", 0.022, 0.6, (px, 0.25, 1.25), CHARCOAL, axis="Y",
        verts=8)
box("StairStr", (0.6, 0.9, 0.05), (-2.55, -0.4, 0.30), STEEL,
    rot=(0.0, 0.45, 0.0))
box("IDPlate", (0.02, 0.25, 0.13), (2.51, 0, 0.45), WARMWHITE, chamfer=False)

export("SM_LB_Paint_SealerDeck_v001", "PaintShop/SealerDeck_v001")
preview("SM_LB_Paint_SealerDeck_v001", "PaintShop/SealerDeck_v001")
