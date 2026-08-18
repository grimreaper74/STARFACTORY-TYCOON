"""Powertrain marriage station v002, fully detailed. v001 was boxes and failed the bar.

The Cairnwell 2040 is fully electric, so this decks a high-voltage battery pack and a
drive unit rather than an engine and gearbox. Real scissor linkages under both lift
tables, flanged and gusseted alignment towers with cable trays, a carrier beam with a
running trolley and chain hoist, and a louvred HV interlock cabinet.
"""
import math
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, RED, STEEL, WARMWHITE, YELLOW, box,
                          column, cyl, export, preview, reset, scissor)

reset()
W, D = 6.4, 4.4

# Foundation: frame, walk-on grate, and the painted cell outline.
box("BaseFrame", (W, D, 0.28), (0, 0, 0.14), CHARCOAL)
box("BaseGrate", (W - 0.6, D - 0.6, 0.05), (0, 0, 0.30), STEEL)
for sx in (-1, 1):
    box("OutlineX", (0.14, D, 0.03), (sx * (W / 2 - 0.07), 0, 0.30), YELLOW)
for sy in (-1, 1):
    box("OutlineY", (W, 0.14, 0.03), (0, sy * (D / 2 - 0.07), 0.30), YELLOW)

# Battery pack lift table on crossed scissor arms with a hydraulic ram.
box("PackDeck", (2.7, 1.7, 0.14), (-0.6, 0, 0.92), STEEL)
for sy in (-1, 1):
    box("PackRail", (2.7, 0.09, 0.13), (-0.6, sy * 0.86, 1.03), YELLOW)
    scissor("PackScissor", (-0.6, sy * 0.62, 0.60), 1.9, 0.55, CHARCOAL)
box("PackHyd", (0.5, 0.22, 0.22), (-0.6, 0, 0.45), GREEN)
cyl("PackRam", 0.06, 0.55, (-0.6, 0, 0.66), STEEL)
box("PackPad", (2.4, 1.4, 0.07), (-0.6, 0, 1.02), WARMWHITE)

# Drive unit table at the front axle position, same mechanism smaller.
box("DriveDeck", (1.3, 1.1, 0.13), (2.05, 0, 0.84), STEEL)
scissor("DriveScissor", (2.05, 0, 0.55), 0.95, 0.48, CHARCOAL)
box("DriveHyd", (0.34, 0.2, 0.2), (2.05, 0, 0.42), GREEN)

# Four alignment towers guide the body down onto the pack.
for sx in (-1, 1):
    for sy in (-1, 1):
        at = (sx * (W / 2 - 0.5), sy * (D / 2 - 0.45), 0.28)
        column("Tower", at, 2.3, GREEN)
        cyl("TowerCone", 0.1, 0.26, (at[0], at[1], 2.72), STEEL)

# Carrier beam: I-section with a running trolley and chain hoist.
box("CrossBeam", (0.36, D + 0.5, 0.42), (0.2, 0, 2.86), GREEN)
box("BeamWeb", (0.14, D + 0.5, 0.3), (0.2, 0, 2.86), CHARCOAL, chamfer=False)
box("Trolley", (0.55, 0.62, 0.24), (0.2, 0.55, 2.58), CHARCOAL)
for sy in (0.42, 0.68):
    cyl("TrolleyWheel", 0.07, 0.06, (0.2, sy, 2.66), STEEL, axis="Y")
cyl("HoistBlock", 0.12, 0.34, (0.2, 0.55, 2.32), CHARCOAL)
cyl("HoistChain", 0.022, 1.0, (0.2, 0.55, 1.78), STEEL)
box("HoistHook", (0.1, 0.16, 0.18), (0.2, 0.55, 1.24), STEEL)

# HV interlock cabinet - characteristic of an EV line - louvred, banded, conduited.
box("HVCab", (0.85, 0.45, 1.6), (-W / 2 + 0.55, -D / 2 + 0.4, 0.92), GREEN)
box("HVBand", (0.87, 0.47, 0.13), (-W / 2 + 0.55, -D / 2 + 0.4, 1.58), YELLOW)
for n in range(4):
    box("HVLouvre", (0.6, 0.02, 0.035),
        (-W / 2 + 0.55, -D / 2 + 0.18, 1.05 + n * 0.11), CHARCOAL, chamfer=False)
cyl("HVConduit", 0.05, 0.85, (-W / 2 + 1.05, -D / 2 + 0.4, 1.55), STEEL)

# Operator station: raked HMI head and a single e-stop in Signal Red.
box("HMIPost", (0.2, 0.2, 1.0), (W / 2 - 0.6, -D / 2 + 0.45, 0.78), CHARCOAL)
box("HMIHead", (0.62, 0.2, 0.44), (W / 2 - 0.6, -D / 2 + 0.45, 1.38), GREEN,
    rot=(math.radians(-18.0), 0.0, 0.0))
box("HMIScreen", (0.5, 0.04, 0.3), (W / 2 - 0.6, -D / 2 + 0.36, 1.4), WARMWHITE,
    rot=(math.radians(-18.0), 0.0, 0.0))
cyl("EStop", 0.07, 0.07, (W / 2 - 0.6, -D / 2 + 0.34, 1.08), RED, axis="Y")

export("SM_LB_Assembly_PowertrainMarriage_v003", "AssemblyShop/PowertrainMarriage_v003")
preview("SM_LB_Assembly_PowertrainMarriage_v003", "AssemblyShop/PowertrainMarriage_v003")
