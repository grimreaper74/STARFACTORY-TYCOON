"""Paint polish deck: the finesse deck flanking the line after topcoat.

Recognised by the low grated deck on legs with its outer railing, the
overhead inspection lamp rail washing the line side, the two docked
orbital polisher heads, and the pad rack. Line side faces south.
"""
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, STEEL, WARMWHITE, box, cyl, export,
                          preview, reset)

reset()

# Deck on legs with grating strips and kick plates.
for lx in (-2.8, 0.0, 2.8):
    for ly in (-0.6, 0.6):
        box("Leg", (0.1, 0.1, 0.3), (lx, ly, 0.15), CHARCOAL, chamfer=False)
box("Deck", (6.0, 1.6, 0.12), (0, 0, 0.36), GREEN)
for n in range(11):
    box("Grate", (0.04, 1.5, 0.015), (-2.75 + n * 0.55, 0, 0.43), STEEL,
        chamfer=False)
for ky in (-0.79, 0.79):
    box("KickPlate", (6.0, 0.03, 0.1), (0, ky, 0.47), CHARCOAL,
        chamfer=False)

# Outer railing on the north edge.
for px in (-2.9, -1.45, 0.0, 1.45, 2.9):
    box("RailPost", (0.06, 0.06, 1.0), (px, 0.76, 0.92), GREEN)
for rz in (1.4, 1.0):
    box("Rail", (6.0, 0.05, 0.06), (0, 0.76, rz), GREEN)

# Lamp rail washing the line side.
for ax in (-2.6, 2.6):
    box("LampPost", (0.1, 0.1, 2.6), (ax, 0.5, 1.72), GREEN)
box("LampBoom", (5.6, 0.1, 0.1), (0, 0.5, 3.02), GREEN)
for n, sx in enumerate((-1.9, 0.0, 1.9)):
    box("LampHead", (0.9, 0.16, 0.08), (sx, 0.38, 2.94), WARMWHITE,
        rot=(0.5, 0.0, 0.0), chamfer=False)

# Docked orbital polishers and the pad rack.
for hx in (-1.0, 1.0):
    box("ToolPost", (0.08, 0.08, 0.7), (hx, 0.45, 0.77), CHARCOAL)
    box("Holster", (0.14, 0.12, 0.14), (hx, 0.38, 1.12), STEEL)
    cyl("PolisherBody", 0.07, 0.24, (hx, 0.3, 1.3), GREEN, verts=12)
    cyl("PolisherPad", 0.13, 0.04, (hx, 0.3, 1.16), CHARCOAL, verts=16)
box("PadRackBase", (0.24, 0.24, 0.06), (2.5, 0.4, 0.45), CHARCOAL)
cyl("PadRod", 0.02, 0.6, (2.5, 0.4, 0.75), STEEL, verts=8)
for n in range(5):
    cyl("Pad", 0.11, 0.028, (2.5, 0.4, 0.52 + n * 0.05), WARMWHITE,
        verts=16)
box("Placard", (0.3, 0.02, 0.16), (-2.6, -0.81, 0.47), WARMWHITE,
    chamfer=False)

export("SM_LB_Paint_PolishDeck_v001", "PaintShop/PolishDeck_v001")
preview("SM_LB_Paint_PolishDeck_v001", "PaintShop/PolishDeck_v001")
