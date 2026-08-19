"""Weld metal finish bench: the robotic finishing station at the quality gate.

Recognised by the heavy bench with its panel rest fixture, the dolly block
row, the automated tool rack behind with sander heads, the task light bar,
and the extraction hood with its duct rising off the top.
"""
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, STEEL, WARMWHITE, box, cyl, export,
                          preview, reset)

reset()

# Heavy bench with shelf and levelling feet.
box("BenchTop", (2.2, 1.0, 0.12), (0, 0, 0.92), CHARCOAL)
box("BenchFrame", (2.1, 0.9, 0.10), (0, 0, 0.82), GREEN)
for lx in (-0.95, 0.95):
    for ly in (-0.38, 0.38):
        box("Leg", (0.09, 0.09, 0.78), (lx, ly, 0.39), GREEN)
        cyl("Foot", 0.035, 0.05, (lx, ly, 0.025), STEEL, verts=8)
box("Shelf", (2.0, 0.85, 0.04), (0, 0, 0.30), STEEL)

# Panel rest fixture and dolly block row on the top.
box("PanelRest", (0.9, 0.55, 0.08), (-0.45, 0, 1.02), STEEL,
    rot=(0.0, -0.15, 0.0))
for n in range(4):
    box("Dolly", (0.12, 0.10, 0.10), (0.45 + n * 0.17, -0.32, 1.03),
        CHARCOAL)

# Tool rack behind with sander heads and cable hooks.
box("RackBack", (2.0, 0.06, 0.9), (0, 0.52, 1.55), GREEN)
for n in range(3):
    cyl("SanderBody", 0.07, 0.22, (-0.6 + n * 0.6, 0.45, 1.55), CHARCOAL,
        axis="Y", verts=12)
    cyl("SanderPad", 0.09, 0.03, (-0.6 + n * 0.6, 0.32, 1.55), STEEL,
        axis="Y", verts=14)
for n in range(2):
    cyl("CableHook", 0.05, 0.04, (-0.3 + n * 0.6, 0.48, 1.25), STEEL,
        axis="Y", verts=10)

# Task light bar and the extraction hood with duct.
box("LightBar", (1.8, 0.10, 0.05), (0, 0.1, 2.05), CHARCOAL)
box("LightLens", (1.6, 0.06, 0.03), (0, 0.06, 2.03), WARMWHITE,
    chamfer=False)
for px in (-0.95, 0.95):
    box("HoodPost", (0.06, 0.06, 1.1), (px, 0.3, 1.55), STEEL)
box("Hood", (2.2, 1.0, 0.25), (0, 0, 2.25), GREEN)
cyl("Duct", 0.14, 0.8, (0.6, 0.2, 2.75), STEEL, verts=14)
cyl("DuctBend", 0.14, 0.3, (0.75, 0.2, 3.12), STEEL, axis="X", verts=14)
box("IDPlate", (0.02, 0.2, 0.11), (-1.11, 0, 0.7), WARMWHITE, chamfer=False)

export("SM_LB_Weld_MetalFinishBench_v001", "WeldShop/MetalFinishBench_v001")
preview("SM_LB_Weld_MetalFinishBench_v001", "WeldShop/MetalFinishBench_v001")
