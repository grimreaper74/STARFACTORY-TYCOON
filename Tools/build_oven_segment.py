"""Paint shop ED oven segment: 6 m of the 72 m enclosed curing oven.

Recognised by its insulated panel shell with visible panel seams, the two
roof recirculation fan units with cowls and ducts, the side burner box with
its flue, and the inspection door with a porthole light. The carrier slot
runs along the roof centreline.
"""
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, RED, STEEL, WARMWHITE, YELLOW, box,
                          cyl, export, preview, reset)

reset()

L, W = 6.0, 4.2
Z0, Z1 = 0.5, 4.6  # shell band

# Support legs and the insulated shell with panel seams.
for lx in (-2.6, 0.0, 2.6):
    for sy in (-W * 0.5 + 0.2, W * 0.5 - 0.2):
        box("Leg", (0.20, 0.20, Z0), (lx, sy, Z0 * 0.5), CHARCOAL)
box("Shell", (L, W, Z1 - Z0), (0, 0, (Z0 + Z1) * 0.5), GREEN)
for n in range(3):
    sx = -L * 0.5 + 1.5 + n * 1.5
    box("SeamV", (0.08, W + 0.06, Z1 - Z0), (sx, 0, (Z0 + Z1) * 0.5),
        CHARCOAL, chamfer=False)
for sy in (-W * 0.5, W * 0.5):
    box("SeamH", (L, 0.07, 0.10), (0, sy * 1.008, 2.5), CHARCOAL,
        chamfer=False)
box("SkirtBand", (L, W + 0.05, 0.18), (0, 0, Z0 + 0.09), CHARCOAL,
    chamfer=False)

# Roof carrier slot with heat-seal brushes either side.
box("RoofSlot", (L, 0.30, 0.12), (0, 0, Z1 + 0.05), CHARCOAL, chamfer=False)
for sy in (-0.22, 0.22):
    box("SlotBrush", (L, 0.06, 0.08), (0, sy, Z1 + 0.07), STEEL,
        chamfer=False)

# Two recirculation fan units on the roof.
for fx in (-1.5, 1.5):
    box("FanPlinth", (1.1, 1.1, 0.25), (fx, 0.9, Z1 + 0.12), CHARCOAL)
    cyl("FanCowl", 0.42, 0.55, (fx, 0.9, Z1 + 0.55), GREEN, verts=20)
    cyl("FanCap", 0.46, 0.08, (fx, 0.9, Z1 + 0.86), CHARCOAL, verts=20)
    cyl("FanDuct", 0.16, 0.8, (fx, 0.35, Z1 + 0.35), STEEL, axis="Y",
        verts=14)

# Burner box and flue on the south wall.
box("BurnerBox", (1.4, 0.7, 1.1), (-1.6, -W * 0.5 - 0.36, 1.6), GREEN)
box("BurnerPanel", (0.5, 0.02, 0.4), (-1.6, -W * 0.5 - 0.72, 1.7), CHARCOAL,
    chamfer=False)
cyl("Flue", 0.14, 2.6, (-1.6, -W * 0.5 - 0.36, 3.4), STEEL, verts=14)
cyl("FlueCap", 0.18, 0.08, (-1.6, -W * 0.5 - 0.36, 4.74), CHARCOAL, verts=14)
cyl("GasLine", 0.03, 1.2, (-2.2, -W * 0.5 - 0.36, 0.7), YELLOW, verts=10)

# Inspection door with porthole and pilot light.
box("Door", (0.7, 0.06, 1.5), (1.8, -W * 0.5 - 0.02, 1.5), GREEN)
box("DoorFrame", (0.8, 0.04, 1.6), (1.8, -W * 0.5 - 0.005, 1.5), CHARCOAL,
    chamfer=False)
cyl("Porthole", 0.10, 0.05, (1.8, -W * 0.5 - 0.06, 1.9), WARMWHITE, axis="Y",
    verts=14)
cyl("DoorHandle", 0.015, 0.16, (2.05, -W * 0.5 - 0.07, 1.45), STEEL, verts=8)
cyl("PilotLight", 0.035, 0.05, (1.35, -W * 0.5 - 0.06, 2.3), RED, axis="Y")
box("IDPlate", (0.3, 0.02, 0.15), (0.4, -W * 0.5 - 0.05, 2.6), WARMWHITE,
    chamfer=False)

export("SM_LB_Paint_OvenSegment_v003", "PaintShop/OvenSegment_v003")
preview("SM_LB_Paint_OvenSegment_v003", "PaintShop/OvenSegment_v003")
