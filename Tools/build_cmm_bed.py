"""Weld shop CMM bed: the coordinate measuring machine at the quality gate.

Recognised by its granite-dark bed on isolation mounts, the moving bridge
with its carriage and vertical probe quill, the probe head with stylus,
and the open enclosure frame with light-curtain posts.
"""
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, STEEL, WARMWHITE, YELLOW, box, cyl,
                          export, preview, reset)

reset()

# Granite bed on isolation mounts.
for mx in (-2.0, 0.0, 2.0):
    for my in (-0.9, 0.9):
        cyl("IsoMount", 0.12, 0.20, (mx, my, 0.10), CHARCOAL, verts=14)
box("Bed", (4.6, 2.2, 0.45), (0, 0, 0.43), CHARCOAL)
box("BedSkirt", (4.7, 2.3, 0.06), (0, 0, 0.18), GREEN)

# Bridge on columns riding the bed rails.
for sy in (-1.0, 1.0):
    box("BedRail", (4.4, 0.10, 0.06), (0, sy, 0.69), STEEL, chamfer=False)
for sy in (-1.05, 1.05):
    box("BridgeCol", (0.30, 0.16, 1.10), (0.4, sy, 1.21), GREEN)
box("BridgeBeam", (0.30, 2.4, 0.28), (0.4, 0, 1.85), GREEN)
box("Carriage", (0.34, 0.30, 0.36), (0.4, -0.3, 1.83), CHARCOAL)
box("Quill", (0.10, 0.10, 0.90), (0.4, -0.3, 1.30), STEEL)
cyl("ProbeHead", 0.055, 0.12, (0.4, -0.3, 0.82), CHARCOAL, verts=14)
cyl("Stylus", 0.008, 0.10, (0.4, -0.3, 0.72), STEEL, verts=6)

# A BIW underbody fixture plate with rest pins on the bed.
box("FixPlate", (1.6, 1.0, 0.06), (-1.0, 0, 0.71), STEEL)
for px in (-1.5, -0.5):
    for py in (-0.35, 0.35):
        cyl("RestPin", 0.03, 0.20, (px, py, 0.83), CHARCOAL, verts=8)

# Enclosure frame with light-curtain posts and controller.
for ex in (-2.5, 2.5):
    for ey in (-1.25, 1.25):
        box("FramePost", (0.08, 0.08, 2.2), (ex, ey, 1.1), GREEN)
for ex in (-2.5, 2.5):
    box("FrameRail", (0.06, 2.5, 0.06), (ex, 0, 2.18), GREEN, chamfer=False)
for ey in (-1.25, 1.25):
    box("FrameRailX", (5.0, 0.06, 0.06), (0, ey, 2.18), GREEN, chamfer=False)
for cy in (-1.25, 1.25):
    cyl("Curtain", 0.03, 1.7, (2.5, cy, 0.95), STEEL, verts=10)
    box("CurtainFoot", (0.10, 0.10, 0.04), (2.5, cy, 0.04), CHARCOAL,
        chamfer=False)
box("Controller", (0.45, 0.35, 1.1), (-2.75, 0.9, 0.55), GREEN)
box("CtrlScreen", (0.02, 0.24, 0.16), (-2.98, 0.9, 0.85), WARMWHITE,
    chamfer=False)
box("IDPlate", (0.02, 0.24, 0.13), (-2.31, 0, 0.5), WARMWHITE, chamfer=False)

export("SM_LB_Weld_CMMBed_v001", "WeldShop/CMMBed_v001")
preview("SM_LB_Weld_CMMBed_v001", "WeldShop/CMMBed_v001")
