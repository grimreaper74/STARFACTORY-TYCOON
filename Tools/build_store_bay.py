"""Assembly painted-body store bay: two slots wide, two decks high.

Tiles into the 24-slot store. Recognised by its six posts with base plates,
the two deck levels of sill rails per slot, the rear X-bracing, the entry
guide funnels, and slot placards. Bodies rest on the rails at import.
"""
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, STEEL, WARMWHITE, YELLOW, box, cyl,
                          export, preview, reset)

reset()

H = 4.6

# Six posts on base plates, three column lines for two slots.
for sx in (-2.35, 2.35):
    for sy in (-2.2, 0.0, 2.2):
        box("PostPlate", (0.34, 0.34, 0.04), (sx, sy, 0.02), CHARCOAL,
            chamfer=False)
        box("Post", (0.20, 0.20, H), (sx, sy, H * 0.5), GREEN)
        box("PostCap", (0.24, 0.24, 0.05), (sx, sy, H + 0.03), CHARCOAL,
            chamfer=False)

# Deck beams at both levels, front and rear.
for dz in (0.45, 2.65):
    for sx in (-2.35, 2.35):
        box("DeckBeam", (0.16, 4.60, 0.20), (sx, 0, dz), GREEN)
    # Sill rails per slot, running the depth of the bay.
    for slot in (-1.1, 1.1):
        for ry in (-0.55, 0.55):
            box("SillRail", (4.60, 0.12, 0.12), (0, slot + ry, dz + 0.16),
                STEEL)
    for slot in (-1.1, 1.1):
        box("EndStop", (0.10, 1.30, 0.16), (2.25, slot, dz + 0.18), YELLOW)

# Rear X-bracing between column lines.
for sy in (-1.1, 1.1):
    for sign in (1.0, -1.0):
        box("RearBrace", (0.06, 2.90, 0.08), (2.42, sy, 1.55), CHARCOAL,
            rot=(sign * 0.72, 0.0, 0.0))

# Entry guide funnels and slot placards at the front.
for slot in (-1.1, 1.1):
    for fy in (-0.75, 0.75):
        box("Funnel", (0.35, 0.05, 0.30), (-2.45, slot + fy, 0.60), STEEL,
            rot=(0.0, 0.0, 0.5 * (1 if fy > 0 else -1)), chamfer=False)
    box("Placard", (0.02, 0.30, 0.18), (-2.44, slot, 0.45), WARMWHITE,
        chamfer=False)

export("SM_LB_Assembly_StoreBay_v001", "AssemblyShop/StoreBay_v001")
preview("SM_LB_Assembly_StoreBay_v001", "AssemblyShop/StoreBay_v001")
