"""Paint sander deck: the scuff/sanding sibling of the polish deck.

Same low grated deck and railing family, but recognised by its dust
extraction set: the extraction cabinet with its boom and two flex drops,
docked orbital sanders, the abrasive disc rack, and the darker downdraft
strip along the line edge.
"""
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, STEEL, WARMWHITE, box, cyl, export,
                          preview, reset)

reset()

for lx in (-2.8, 0.0, 2.8):
    for ly in (-0.6, 0.6):
        box("Leg", (0.1, 0.1, 0.3), (lx, ly, 0.15), CHARCOAL, chamfer=False)
box("Deck", (6.0, 1.6, 0.12), (0, 0, 0.36), GREEN)
for n in range(11):
    box("Grate", (0.04, 1.5, 0.015), (-2.75 + n * 0.55, 0, 0.43), STEEL,
        chamfer=False)
# Downdraft strip along the line edge.
box("Downdraft", (5.6, 0.3, 0.02), (0, -0.6, 0.435), CHARCOAL,
    chamfer=False)
for ky in (-0.79, 0.79):
    box("KickPlate", (6.0, 0.03, 0.1), (0, ky, 0.47), CHARCOAL,
        chamfer=False)
for px in (-2.9, -1.45, 0.0, 1.45, 2.9):
    box("RailPost", (0.06, 0.06, 1.0), (px, 0.76, 0.92), GREEN)
for rz in (1.4, 1.0):
    box("Rail", (6.0, 0.05, 0.06), (0, 0.76, rz), GREEN)

# Extraction cabinet with boom and flex drops.
box("ExtractCabinet", (0.9, 0.7, 1.5), (2.4, 0.35, 1.17), GREEN)
box("CabinetCap", (0.96, 0.76, 0.06), (2.4, 0.35, 1.95), CHARCOAL)
box("FilterGrille", (0.02, 0.5, 0.6), (1.94, 0.35, 1.0), STEEL,
    chamfer=False)
box("Boom", (3.6, 0.12, 0.12), (0.3, 0.35, 2.04), GREEN)
box("BoomPost", (0.08, 0.08, 1.56), (-1.4, 0.35, 1.2), GREEN)
for bx in (-0.9, 0.9):
    cyl("FlexDrop", 0.055, 0.9, (bx, 0.35, 1.62), CHARCOAL, verts=10)
    cyl("DropCuff", 0.07, 0.08, (bx, 0.35, 1.14), STEEL, verts=10)

# Docked orbital sanders and the abrasive disc rack.
for hx in (-0.9, 0.9):
    box("ToolPost", (0.08, 0.08, 0.7), (hx, 0.45, 0.77), CHARCOAL)
    box("Holster", (0.14, 0.12, 0.14), (hx, 0.38, 1.12), STEEL)
    cyl("SanderBody", 0.07, 0.2, (hx, 0.3, 1.28), GREEN, verts=12)
    cyl("SanderPad", 0.11, 0.05, (hx, 0.3, 1.15), CHARCOAL, verts=16)
box("DiscRackBase", (0.24, 0.24, 0.06), (-2.5, 0.4, 0.45), CHARCOAL)
cyl("DiscRod", 0.02, 0.6, (-2.5, 0.4, 0.75), STEEL, verts=8)
for n in range(6):
    cyl("Disc", 0.1, 0.02, (-2.5, 0.4, 0.51 + n * 0.045), WARMWHITE,
        verts=16)
box("Placard", (0.3, 0.02, 0.16), (-2.6, -0.81, 0.47), WARMWHITE,
    chamfer=False)

export("SM_LB_Paint_SanderDeck_v001", "PaintShop/SanderDeck_v001")
preview("SM_LB_Paint_SanderDeck_v001", "PaintShop/SanderDeck_v001")
