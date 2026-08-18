"""Paint shop power-and-free track: one 4 m goalpost segment at ED height.

Enclosed box track with a bottom slot the trolley drops run in, power chain
cover on top, hanger plates to the bridge, bolted butt ends so segments
chain. Rail centre at 5.2 m to match the PF carrier.
"""
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, STEEL, WARMWHITE, box, column, cyl,
                          export, preview, reset)

reset()

for sy in (-1.7, 1.7):
    column("Post", (0, sy, 0), 5.35, GREEN, width=0.30)
box("Bridge", (0.55, 3.8, 0.34), (0, 0, 5.70), GREEN)
for sy in (-1.62, 1.62):
    box("BridgeGusset", (0.40, 0.14, 0.30), (0, sy, 5.48), CHARCOAL)

# Enclosed track box with the bottom running slot.
box("TrackBox", (4.0, 0.32, 0.26), (0, 0, 5.33), CHARCOAL)
for sy in (-0.12, 0.12):
    box("SlotFlange", (4.0, 0.08, 0.05), (0, sy, 5.17), STEEL, chamfer=False)
box("ChainCover", (4.0, 0.18, 0.10), (0, 0, 5.50), GREEN)
for hx in (-1.5, 0.0, 1.5):
    box("HangerPlate", (0.16, 0.06, 0.16), (hx, 0, 5.55), CHARCOAL)
for ex in (-1.99, 1.99):
    box("ButtPlate", (0.03, 0.40, 0.36), (ex, 0, 5.33), CHARCOAL,
        chamfer=False)
    for by in (-0.14, 0.14):
        cyl("ButtBolt", 0.016, 0.05, (ex, by, 5.33), STEEL, axis="X", verts=8)
box("InspectionHatch", (0.5, 0.34, 0.06), (0.8, 0, 5.48), STEEL)
box("HatchLatch", (0.08, 0.05, 0.04), (1.02, 0, 5.50), CHARCOAL,
    chamfer=False)
box("IDPlate", (0.02, 0.20, 0.12), (0.16, -1.72, 3.2), WARMWHITE,
    chamfer=False)

export("SM_LB_Paint_PFTrackSegment_v001", "PaintShop/PFTrack_v001")
preview("SM_LB_Paint_PFTrackSegment_v001", "PaintShop/PFTrack_v001")
