"""Weld hemming press: the table-top hemmer that folds closure skins.

Recognised by the C-frame with its crowned head, the lower hem bed with
a door-skin blank on locators, the four corner cam units, the upper
platen on guide pillars, and the hydraulic pack on the rear. The open
throat faces south.
"""
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, STEEL, WARMWHITE, box, cyl, export,
                          preview, reset)

reset()

# Base, bed and the C-frame.
box("Base", (2.4, 1.8, 0.25), (0, 0.1, 0.13), CHARCOAL)
box("BedRiser", (1.9, 1.3, 0.45), (0, 0.05, 0.48), GREEN)
box("HemBed", (1.7, 1.15, 0.14), (0, 0, 0.78), STEEL)
# Door-skin blank sitting on the bed locators.
box("Blank", (1.15, 0.8, 0.03), (0, -0.05, 0.87), WARMWHITE, chamfer=False)
for lx in (-0.62, 0.62):
    for ly in (-0.42, 0.35):
        cyl("Locator", 0.03, 0.1, (lx, ly, 0.88), CHARCOAL, verts=8)

# Four corner cam units around the bed.
for cx in (-0.95, 0.95):
    for cy in (-0.52, 0.45):
        box("CamUnit", (0.24, 0.2, 0.3), (cx, cy, 0.95), GREEN)
        box("CamBlade", (0.16, 0.05, 0.12), (cx + (0.12 if cx < 0 else -0.12),
            cy, 1.02), STEEL, chamfer=False)

# Rear columns carrying the crowned head over guide pillars.
for px in (-0.75, 0.75):
    box("Column", (0.3, 0.35, 1.9), (px, 0.75, 1.2), GREEN)
box("Crown", (2.2, 1.0, 0.55), (0, 0.35, 2.35), GREEN)
box("CrownCap", (2.26, 1.06, 0.08), (0, 0.35, 2.66), CHARCOAL)
for gx in (-0.55, 0.55):
    cyl("GuidePillar", 0.07, 0.9, (gx, 0.0, 1.6), STEEL, verts=12)
box("Platen", (1.5, 0.95, 0.16), (0, 0.0, 1.18), CHARCOAL)
cyl("MainRam", 0.14, 1.0, (0, 0.2, 1.75), STEEL, verts=14)

# Hydraulic pack and controls on the rear face.
box("HydraulicTank", (0.9, 0.4, 0.5), (0, 1.15, 0.6), GREEN)
cyl("HydraulicMotor", 0.14, 0.4, (0.55, 1.15, 0.62), STEEL, axis="X",
    verts=12)
for hy in (0.45, 0.75):
    cyl("Hose", 0.03, 0.75, (0.75, 0.9, 1.3 - (hy - 0.45)), CHARCOAL,
        verts=8)
box("HMIPanel", (0.4, 0.06, 0.3), (-0.95, 0.72, 1.5), WARMWHITE)
box("Placard", (0.3, 0.02, 0.16), (0.7, -0.6, 0.55), WARMWHITE,
    chamfer=False)

export("SM_LB_Weld_HemmingPress_v001", "WeldShop/HemmingPress_v001")
preview("SM_LB_Weld_HemmingPress_v001", "WeldShop/HemmingPress_v001")
