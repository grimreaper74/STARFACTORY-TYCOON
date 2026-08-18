"""Weld shop index turntable: a two-position rotary table that swaps fixtures.

A turntable is recognised by its circular base with the rotating platform on
top, the divider wall across the middle, and mirrored fixture plates with geo
pins and clamps on either side. The drive housing at the rim and the rotary
union on the divider crown say it indexes under power.
"""
import math
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, RED, STEEL, WARMWHITE, YELLOW, box,
                          cyl, export, preview, reset)

reset()

# ---- base ring, rotation stripe and platform --------------------------------
cyl("BaseRing", 1.05, 0.12, (0, 0, 0.06), CHARCOAL, verts=28)
cyl("SwingStripe", 1.07, 0.03, (0, 0, 0.135), YELLOW, verts=28)
cyl("Platform", 0.95, 0.10, (0, 0, 0.20), GREEN, verts=28)
cyl("SlewRing", 0.99, 0.05, (0, 0, 0.14), STEEL, verts=28)

# ---- divider wall across the middle ------------------------------------------
box("Divider", (0.10, 1.70, 1.44), (0, 0, 0.98), GREEN)
for rz in (0.62, 1.22):
    box("DividerRib", (0.14, 1.70, 0.07), (0, 0, rz), CHARCOAL)
for sy in (-0.55, 0.0, 0.55):
    box("DividerStiff", (0.14, 0.07, 1.40), (0, sy, 0.98), CHARCOAL)
# Mesh band across the top quarter: dark inset behind thin verticals.
box("MeshInset", (0.05, 1.66, 0.34), (0, 0, 1.88), CHARCOAL, chamfer=False)
for n in range(11):
    box("MeshBar", (0.02, 0.015, 0.34), (0.035, -0.75 + n * 0.15, 1.88),
        STEEL, chamfer=False)
for s in (-1.0, 1.0):
    box("WallGusset", (0.42, 0.09, 0.30), (s * 0.24, 0, 0.36), CHARCOAL,
        rot=(0.0, s * -0.55, 0.0))
for sy in (-0.86, 0.86):
    box("DividerPost", (0.13, 0.13, 1.85), (0, sy, 1.18), CHARCOAL)
box("DividerRail", (0.13, 1.85, 0.10), (0, 0, 2.10), CHARCOAL)
cyl("RotaryUnion", 0.09, 0.28, (0, 0, 2.30), STEEL)
cyl("UnionCollar", 0.12, 0.05, (0, 0, 2.18), CHARCOAL)
cyl("Beacon", 0.045, 0.10, (0, 0, 2.50), RED)
cyl("DividerConduit", 0.02, 1.7, (0.07, 0.4, 1.25), STEEL, verts=10)

# ---- mirrored fixture plates with pins and clamps -----------------------------
for sx in (-1.0, 1.0):
    box("FixturePlate", (0.72, 1.24, 0.08), (sx * 0.50, 0, 0.29), STEEL)
    for py in (-0.45, 0.45):
        for px in (-0.22, 0.22):
            cyl("GeoPin", 0.028, 0.16, (sx * 0.50 + px, py, 0.41), STEEL,
                verts=10)
    for py in (-0.30, 0.30):
        box("ClampBlock", (0.14, 0.12, 0.16), (sx * 0.72, py, 0.41), CHARCOAL)
        box("ClampArm", (0.20, 0.06, 0.05), (sx * 0.62, py, 0.50), STEEL)
    for py in (-0.38, 0.38):
        box("JigPylon", (0.15, 0.15, 0.42), (sx * 0.45, py, 0.54), CHARCOAL)
        box("NestSaddle", (0.20, 0.10, 0.07), (sx * 0.45, py, 0.78), STEEL)
    for py in (-0.30, 0.30):
        cyl("ClampCyl", 0.035, 0.16, (sx * 0.72, py, 0.55), CHARCOAL,
            verts=12)
        cyl("ClampRod", 0.014, 0.10, (sx * 0.72, py, 0.66), STEEL, verts=8)

# ---- drive housing and motor at the rim ---------------------------------------
box("DriveHousing", (0.48, 0.42, 0.34), (1.14, 0, 0.17), CHARCOAL)
cyl("DriveMotor", 0.09, 0.30, (1.44, 0, 0.17), GREEN, axis="X")
for n in range(4):
    cyl("MotorFin", 0.095, 0.02, (1.33 + n * 0.06, 0, 0.17), CHARCOAL,
        axis="X", verts=16)
box("DriveCover", (0.30, 0.30, 0.06), (1.05, 0, 0.37), GREEN)

# ---- HMI pedestal and scanner wedges ------------------------------------------
cyl("HMIPost", 0.035, 1.05, (-0.95, -1.2, 0.52), STEEL, verts=12)
box("HMIBody", (0.26, 0.08, 0.20), (-0.95, -1.2, 1.12), GREEN,
    rot=(math.radians(25.0), 0.0, 0.0))
box("HMIScreen", (0.20, 0.02, 0.14), (-0.95, -1.235, 1.13), WARMWHITE,
    rot=(math.radians(25.0), 0.0, 0.0), chamfer=False)
cyl("HMIEStop", 0.04, 0.05, (-0.95, -1.2, 0.94), RED, axis="Y")
for sx, sy in ((-1.15, -1.0), (1.15, 1.0)):
    box("ScannerBase", (0.14, 0.14, 0.08), (sx, sy, 0.04), CHARCOAL,
        chamfer=False)
    box("Scanner", (0.10, 0.10, 0.10), (sx, sy, 0.13), YELLOW)

export("SM_LB_Weld_IndexTurntable_v001", "WeldShop/IndexTurntable_v001")
preview("SM_LB_Weld_IndexTurntable_v001", "WeldShop/IndexTurntable_v001")
