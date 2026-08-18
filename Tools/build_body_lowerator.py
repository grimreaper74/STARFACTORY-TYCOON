"""Assembly body lowerator: the vertical lift dropping bodies off the
overhead store line onto the trim skillet at station 1.

Recognised by its two lattice guide towers, the cradle platform riding
between them with sill rails, the drive house on the crown with twin chain
runs down to the cradle, and the counterweight box on the outside of one
tower. Modelled with the cradle at mid-descent.
"""
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, RED, STEEL, WARMWHITE, YELLOW, box,
                          column, cyl, export, preview, reset)

reset()

H = 6.2

# Guide towers with lattice bracing.
for sx in (-2.6, 2.6):
    for sy in (-0.5, 0.5):
        box("TowerChord", (0.18, 0.18, H), (sx, sy, H * 0.5), GREEN)
    for n in range(5):
        bz = 0.8 + n * 1.15
        box("TowerBrace", (0.07, 1.05, 0.09), (sx, 0, bz), CHARCOAL,
            rot=(0.55 if n % 2 else -0.55, 0.0, 0.0))
    box("TowerFoot", (0.55, 1.30, 0.10), (sx, 0, 0.05), CHARCOAL)
    box("GuideRail", (0.06, 0.10, H - 0.4), (sx - (0.14 if sx > 0 else -0.14),
        0, (H - 0.4) * 0.5 + 0.2), STEEL, chamfer=False)

# Crown drive house with sheaves and twin chains to the cradle.
box("CrownBeam", (5.6, 1.10, 0.35), (0, 0, H + 0.15), GREEN)
box("DriveHouse", (1.4, 0.90, 0.80), (0, 0, H + 0.72), GREEN)
box("HouseVent", (1.0, 0.02, 0.30), (0, -0.46, H + 0.72), CHARCOAL,
    chamfer=False)
for sx in (-1.9, 1.9):
    cyl("Sheave", 0.22, 0.12, (sx, 0, H + 0.18), CHARCOAL, axis="Y", verts=18)
    box("Chain", (0.05, 0.05, 2.6), (sx, 0, H - 1.35), STEEL, chamfer=False)

# Cradle mid-descent with sill rails and end stops.
CZ = 3.4
box("CradleDeck", (4.6, 1.60, 0.16), (0, 0, CZ), CHARCOAL)
for sy in (-0.55, 0.55):
    box("SillRail", (4.2, 0.12, 0.10), (0, sy, CZ + 0.13), STEEL)
for ex in (-2.15, 2.15):
    box("CradleStop", (0.10, 1.4, 0.22), (ex, 0, CZ + 0.16), YELLOW)
for sx in (-2.25, 2.25):
    box("CradleShoe", (0.14, 0.24, 0.40), (sx, 0, CZ), CHARCOAL)

# Counterweight on the east tower and controls at grade.
box("Counterweight", (0.50, 0.70, 1.20), (3.0, 0, 2.2), CHARCOAL)
box("CWGuide", (0.05, 0.60, H - 1.0), (3.05, 0, (H - 1.0) * 0.5 + 0.3),
    STEEL, chamfer=False)
box("Cabinet", (0.5, 0.35, 1.2), (-3.1, 0.8, 0.6), GREEN)
box("CabDoor", (0.02, 0.30, 1.05), (-3.36, 0.8, 0.6), CHARCOAL,
    chamfer=False)
cyl("CabEStop", 0.04, 0.05, (-3.37, 0.72, 0.85), RED, axis="X")
cyl("Beacon", 0.045, 0.10, (0, 0, H + 1.18), RED)
box("IDPlate", (0.02, 0.35, 0.2), (-2.70, 0, 4.5), WARMWHITE, chamfer=False)

export("SM_LB_Assembly_BodyLowerator_v001", "AssemblyShop/BodyLowerator_v001")
preview("SM_LB_Assembly_BodyLowerator_v001", "AssemblyShop/BodyLowerator_v001")
