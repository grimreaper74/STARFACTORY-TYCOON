"""Assembly HV battery install lift: decks the pack up into the body from below.

The Cairnwell 2040 is fully electric (owner decision, 2026-08-18), so the
marriage area's signature machine is this lift: a scissor table carrying the
flat HV pack on a cradle, four nutrunner spindles at the corners to make the
pack-to-body joints, and yellow HV warning covers - the one legitimate use of
yellow beyond floor safety. Modelled mid-raise so it reads in action.
"""
import math
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, RED, STEEL, WARMWHITE, YELLOW, box,
                          cyl, export, preview, reset, scissor)

reset()

# Base frame with bolt pads and approach ramps.
box("Base", (3.30, 1.90, 0.12), (0, 0, 0.06), CHARCOAL)
for bx in (-1.5, 1.5):
    for by in (-0.8, 0.8):
        cyl("BasePad", 0.05, 0.05, (bx, by, 0.14), STEEL, verts=10)
for rx in (-1.72, 1.72):
    box("Ramp", (0.14, 1.6, 0.06), (rx, 0, 0.03), YELLOW,
        rot=(0.0, 0.35 * (1 if rx > 0 else -1), 0.0), chamfer=False)

# Scissor pairs, one each side, and the deck they carry.
for sy in (-0.7, 0.7):
    scissor("Lift", (0, sy, 0.62), 2.4, 0.9, GREEN)
box("Deck", (3.20, 1.80, 0.10), (0, 0, 1.12), GREEN)
box("DeckSkirt", (3.24, 1.84, 0.04), (0, 0, 1.05), CHARCOAL, chamfer=False)

# The HV pack on its cradle: flat slab, module ribs, yellow HV covers.
for cy in (-0.55, 0.0, 0.55):
    box("Cradle", (2.55, 0.14, 0.08), (0, cy, 1.21), CHARCOAL)
box("Pack", (2.40, 1.45, 0.18), (0, 0, 1.34), CHARCOAL)
for n in range(6):
    box("PackRib", (0.30, 1.41, 0.02), (-1.0 + n * 0.4, 0, 1.44), GREEN,
        chamfer=False)
box("HVCoverA", (0.36, 0.30, 0.08), (1.05, 0.45, 1.47), YELLOW)
box("HVCoverB", (0.36, 0.30, 0.08), (1.05, -0.45, 1.47), YELLOW)
cyl("CoolPortA", 0.035, 0.12, (-1.22, 0.35, 1.36), STEEL, axis="X", verts=10)
cyl("CoolPortB", 0.035, 0.12, (-1.22, -0.35, 1.36), STEEL, axis="X", verts=10)

# Corner nutrunner spindles that make the pack-to-body joints.
for sx in (-1.35, 1.35):
    for sy in (-0.62, 0.62):
        box("SpindleBody", (0.14, 0.14, 0.30), (sx, sy, 1.30), CHARCOAL)
        cyl("Spindle", 0.030, 0.42, (sx, sy, 1.62), STEEL, verts=10)
        cyl("SpindleSocket", 0.045, 0.06, (sx, sy, 1.86), CHARCOAL, verts=10)

# Guide posts and the control pendant.
for gx in (-1.58, 1.58):
    cyl("GuidePost", 0.04, 1.5, (gx, 0.88, 0.75), STEEL, verts=12)
box("PendantBox", (0.22, 0.10, 0.30), (1.58, -0.95, 1.10), GREEN)
cyl("PendantEStop", 0.04, 0.04, (1.58, -1.01, 1.18), RED, axis="Y")
cyl("PendantPost", 0.03, 1.0, (1.58, -0.95, 0.50), STEEL, verts=10)

export("SM_LB_Assembly_HVBatteryInstallLift_v001",
       "AssemblyShop/HVBatteryLift_v001")
preview("SM_LB_Assembly_HVBatteryInstallLift_v001",
        "AssemblyShop/HVBatteryLift_v001")
