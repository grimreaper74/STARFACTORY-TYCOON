"""Weld water chiller skid: closed-loop cooling for the weld gun
transformers.

Recognised by the skid frame carrying the chiller cabinet with its
louvred condenser end and twin fans, the insulated buffer tank, the pump
pair with motors, and the flow/return manifold with valve handles.
"""
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, STEEL, WARMWHITE, box, cyl, export,
                          preview, reset)

reset()

# Skid frame with fork channels.
box("SkidFrame", (3.0, 1.4, 0.14), (0, 0, 0.07), CHARCOAL)
for fy in (-0.4, 0.4):
    box("ForkChannel", (3.0, 0.16, 0.1), (0, fy, 0.05), CHARCOAL,
        chamfer=False)

# Chiller cabinet with louvred condenser end and twin roof fans.
box("Cabinet", (1.5, 1.2, 1.5), (-0.65, 0, 0.89), GREEN)
box("CabinetCap", (1.56, 1.26, 0.07), (-0.65, 0, 1.67), CHARCOAL)
box("LouvreFrame", (0.06, 1.0, 1.1), (-1.42, 0, 0.9), CHARCOAL,
    chamfer=False)
for n in range(5):
    box("Slat", (0.05, 0.9, 0.1), (-1.44, 0, 0.5 + n * 0.2), STEEL,
        rot=(0.5, 0.0, 0.0), chamfer=False)
for fy in (-0.3, 0.3):
    cyl("FanShroud", 0.24, 0.12, (-0.65, fy, 1.76), CHARCOAL, verts=18)
    cyl("FanHub", 0.06, 0.14, (-0.65, fy, 1.77), STEEL, verts=10)

# Insulated buffer tank on saddles.
for sx in (0.45, 1.05):
    box("Saddle", (0.12, 0.9, 0.3), (sx, 0, 0.29), CHARCOAL)
cyl("BufferTank", 0.42, 1.3, (0.75, 0, 0.85), STEEL, axis="X", verts=22)
cyl("TankEnd", 0.32, 0.1, (1.45, 0, 0.85), GREEN, axis="X", verts=18)

# Pump pair with motors, feeding the manifold.
for py in (-0.35, 0.35):
    box("PumpBase", (0.4, 0.3, 0.12), (1.15, py, 0.2), CHARCOAL)
    cyl("PumpVolute", 0.11, 0.18, (1.0, py, 0.36), GREEN, axis="X",
        verts=14)
    cyl("PumpMotor", 0.1, 0.32, (1.28, py, 0.36), STEEL, axis="X", verts=14)
box("Manifold", (0.1, 1.1, 0.1), (1.45, 0, 1.3), STEEL)
for py in (-0.35, 0.0, 0.35):
    cyl("ManifoldDrop", 0.04, 1.1, (1.45, py, 0.75), STEEL, verts=8)
    cyl("ValveWheel", 0.07, 0.04, (1.45, py, 1.42), GREEN, verts=12)
box("Placard", (0.02, 0.28, 0.16), (1.51, 0, 0.7), WARMWHITE, chamfer=False)

export("SM_LB_Weld_WaterChillerSkid_v001", "WeldShop/WaterChillerSkid_v001")
preview("SM_LB_Weld_WaterChillerSkid_v001", "WeldShop/WaterChillerSkid_v001")
