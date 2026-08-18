"""Paint pretreatment spray stage: the open wash section before the dip tanks.

Recognised by its three spray ring arches with nozzle studs pointing inward,
the ribbed mist-shield walls either side, the full-length drip grates, and
the chemical feed pipes running along one shield to the rings.
"""
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, STEEL, WARMWHITE, box, cyl, export,
                          preview, reset)

reset()

L = 4.2

# Mist-shield walls with ribs.
for sy in (-2.1, 2.1):
    box("Shield", (L, 0.08, 3.2), (0, sy, 1.75), GREEN)
    for n in range(4):
        box("ShieldRib", (0.12, 0.14, 3.1), (-1.6 + n * 1.05, sy, 1.72),
            CHARCOAL)
    box("ShieldBand", (L, 0.10, 0.2), (0, sy, 1.75), CHARCOAL, chamfer=False)

# Three spray ring arches with inward nozzle studs.
for ax in (-1.4, 0.0, 1.4):
    for sy in (-1.55, 1.55):
        box("RingLeg", (0.12, 0.12, 3.0), (ax, sy, 1.5), STEEL)
    box("RingHead", (0.12, 3.2, 0.12), (ax, 0, 3.05), STEEL)
    for n in range(6):
        cyl("NozzleTop", 0.025, 0.10, (ax, -1.25 + n * 0.5, 2.95), CHARCOAL,
            verts=8)
    for sy in (-1.48, 1.48):
        for nz in (0.9, 1.7, 2.5):
            cyl("NozzleSide", 0.025, 0.10,
                (ax, sy + (0.06 if sy < 0 else -0.06), nz), CHARCOAL,
                axis="Y", verts=8)

# Drip grates and the chemical feed pipes.
for gy in (-0.8, 0.0, 0.8):
    for n in range(3):
        box("DripGrate", (1.3, 0.7, 0.03), (-1.4 + n * 1.4, gy, 0.015),
            STEEL, chamfer=False)
for pz, name in ((2.2, "FeedPipeA"), (2.5, "FeedPipeB")):
    cyl(name, 0.05, L - 0.4, (0, -2.22, pz), STEEL, axis="X", verts=12)
for ax in (-1.4, 0.0, 1.4):
    cyl("FeedDrop", 0.03, 0.6, (ax, -1.9, 2.6), STEEL, verts=8,
        axis="Y")
box("IDPlate", (0.02, 0.3, 0.18), (-2.11, -2.1, 1.6), WARMWHITE,
    chamfer=False)

export("SM_LB_Paint_PretreatSprayStage_v001", "PaintShop/PretreatSpray_v001")
preview("SM_LB_Paint_PretreatSprayStage_v001", "PaintShop/PretreatSpray_v001")
