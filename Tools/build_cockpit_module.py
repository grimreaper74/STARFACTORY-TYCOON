"""Assembly cockpit module staged line-side on its shipping stand.

Recognised by the cross-car beam with its end brackets, the dash top with
the cluster hump, the HVAC core hanging behind, the steering column stub,
and the stillage stand it ships on.
"""
import math
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, STEEL, WARMWHITE, box, cyl, export,
                          preview, reset)

reset()

# Stillage stand.
box("StandBase", (1.60, 0.70, 0.08), (0, 0, 0.04), CHARCOAL)
for sx in (-0.65, 0.65):
    box("StandPost", (0.08, 0.08, 0.70), (sx, 0.18, 0.43), CHARCOAL)
    box("StandArm", (0.08, 0.45, 0.06), (sx, 0, 0.75), CHARCOAL)
box("StandBrace", (1.25, 0.06, 0.05), (0, 0.18, 0.55), CHARCOAL)

# Cross-car beam with end brackets, resting on the arms.
cyl("CrossBeam", 0.045, 1.45, (0, 0, 0.82), STEEL, axis="X", verts=14)
for sx in (-0.70, 0.70):
    box("EndBracket", (0.06, 0.22, 0.30), (sx, 0, 0.85), CHARCOAL)

# Dash top, cluster hump and centre stack.
box("DashTop", (1.35, 0.40, 0.10), (0, -0.06, 0.99), CHARCOAL)
box("DefrosterStrip", (1.20, 0.10, 0.015), (0, 0.05, 1.045), STEEL,
    chamfer=False)
box("DashFace", (1.35, 0.12, 0.28), (0, -0.24, 0.84), CHARCOAL)
box("GloveboxSeam", (0.45, 0.005, 0.20), (0.42, -0.301, 0.84), STEEL,
    chamfer=False)
box("ClusterHump", (0.40, 0.30, 0.14), (-0.38, -0.10, 1.09), CHARCOAL)
box("ClusterFace", (0.30, 0.02, 0.09), (-0.38, -0.255, 1.06), WARMWHITE,
    chamfer=False)
for vx in (-0.60, 0.60):
    box("EndVent", (0.10, 0.02, 0.07), (vx, -0.305, 0.93), STEEL,
        chamfer=False)
box("CentreStack", (0.26, 0.16, 0.30), (0, -0.26, 0.95), GREEN)
box("StackScreen", (0.18, 0.02, 0.12), (0, -0.345, 1.02), WARMWHITE,
    chamfer=False)

# HVAC core behind and the steering column stub.
box("HVACCore", (0.55, 0.30, 0.35), (0.15, 0.16, 0.80), GREEN)
cyl("BlowerScroll", 0.14, 0.20, (0.50, 0.16, 0.82), CHARCOAL, axis="Y",
    verts=16)
for dx in (0.02, 0.28):
    cyl("HVACDuct", 0.05, 0.30, (dx, 0.16, 0.58), CHARCOAL, verts=10)
cyl("ColumnStub", 0.035, 0.40, (-0.38, -0.18, 0.72), STEEL, axis="Y",
    verts=10)
cyl("ColumnUJoint", 0.05, 0.08, (-0.38, -0.36, 0.66), CHARCOAL, axis="Y",
    verts=10)
box("Label", (0.16, 0.01, 0.10), (0.68, -0.15, 0.55), WARMWHITE,
    chamfer=False)

export("SM_LB_Assembly_CockpitModule_v001", "AssemblyShop/CockpitModule_v001")
preview("SM_LB_Assembly_CockpitModule_v001", "AssemblyShop/CockpitModule_v001")
