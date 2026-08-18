"""Paint chemical dosing skid feeding the pretreatment stages.

Recognised by its bunded skid with three dosing tanks, the agitator motors
on the tank lids, the shared dosing manifold with valve wheels, pump pods,
and the level gauges strapped to each tank.
"""
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, RED, STEEL, WARMWHITE, YELLOW, box,
                          cyl, export, preview, reset)

reset()

# Bunded skid.
box("Skid", (3.2, 1.4, 0.14), (0, 0, 0.07), CHARCOAL)
for ly in (-0.68, 0.68):
    box("BundY", (3.2, 0.04, 0.2), (0, ly, 0.17), YELLOW, chamfer=False)
for lx in (-1.58, 1.58):
    box("BundX", (0.04, 1.4, 0.2), (lx, 0, 0.17), YELLOW, chamfer=False)

# Three dosing tanks with lids, agitator motors and level gauges.
for n, tx in enumerate((-1.05, 0.0, 1.05)):
    cyl("Tank", 0.42, 1.5, (tx, 0.1, 0.9), GREEN, verts=22)
    cyl("TankLid", 0.44, 0.08, (tx, 0.1, 1.68), CHARCOAL, verts=22)
    cyl("Agitator", 0.12, 0.25, (tx, 0.1, 1.84), CHARCOAL, verts=14)
    cyl("AgitatorCap", 0.08, 0.10, (tx, 0.1, 2.0), STEEL, verts=12)
    box("LevelGauge", (0.04, 0.06, 1.2), (tx + 0.44, -0.05, 0.95), WARMWHITE,
        chamfer=False)
    for gz in (0.5, 0.95, 1.4):
        box("GaugeClamp", (0.06, 0.08, 0.04), (tx + 0.44, -0.05, gz),
            CHARCOAL, chamfer=False)
    cyl("Outlet", 0.035, 0.30, (tx, -0.35, 0.35), STEEL, axis="Y", verts=10)

# Dosing manifold along the front with valve wheels and pump pods.
cyl("Manifold", 0.045, 2.9, (0, -0.55, 0.35), STEEL, axis="X", verts=12)
for tx in (-1.05, 0.0, 1.05):
    cyl("Valve", 0.09, 0.04, (tx - 0.3, -0.55, 0.47), YELLOW, axis="X",
        verts=12)
for px in (-0.5, 0.6):
    cyl("Pump", 0.14, 0.30, (px, -0.55, 0.62), GREEN, axis="X", verts=14)
    box("PumpBase", (0.34, 0.20, 0.10), (px, -0.55, 0.25), CHARCOAL)
box("Cabinet", (0.36, 0.24, 0.7), (1.62, 0.45, 0.5), GREEN)
cyl("CabEStop", 0.035, 0.04, (1.62, 0.32, 0.75), RED, axis="Y")
box("IDPlate", (0.02, 0.22, 0.12), (-1.62, 0, 0.75), WARMWHITE,
    chamfer=False)

export("SM_LB_Paint_ChemDosingSkid_v001", "PaintShop/ChemDosingSkid_v001")
preview("SM_LB_Paint_ChemDosingSkid_v001", "PaintShop/ChemDosingSkid_v001")
