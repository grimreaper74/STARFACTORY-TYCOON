"""Assembly HVAC module staged line-side on its pallet.

Recognised by the evaporator case with its blower scroll, the round blower
motor, heater hose stubs, drain elbow, and the shipping pallet with corner
blocks. A small part, so silhouette carries it.
"""
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, STEEL, WARMWHITE, box, cyl, export,
                          preview, reset)

reset()

box("Pallet", (0.95, 0.75, 0.10), (0, 0, 0.05), CHARCOAL)
for px in (-0.38, 0.38):
    for py in (-0.28, 0.28):
        box("PalletBlock", (0.12, 0.12, 0.10), (px, py, 0.05), CHARCOAL,
            chamfer=False)
box("EvapCase", (0.60, 0.45, 0.40), (0, 0.02, 0.42), CHARCOAL)
box("CaseSeam", (0.62, 0.02, 0.40), (0, -0.02, 0.42), STEEL, chamfer=False)
cyl("BlowerScroll", 0.17, 0.22, (0.28, -0.10, 0.50), CHARCOAL, axis="Y",
    verts=18)
cyl("BlowerMotor", 0.10, 0.14, (0.28, -0.28, 0.50), GREEN, axis="Y", verts=14)
cyl("DuctStubA", 0.07, 0.14, (-0.18, 0.02, 0.68), STEEL, verts=12)
cyl("DuctStubB", 0.07, 0.14, (0.05, 0.02, 0.68), STEEL, verts=12)
for hy in (-0.06, 0.06):
    cyl("HeaterHose", 0.025, 0.16, (-0.34, hy, 0.52), STEEL, axis="X",
        verts=8)
cyl("DrainElbow", 0.02, 0.12, (-0.15, -0.24, 0.20), STEEL, verts=8)
box("Label", (0.14, 0.01, 0.09), (0.1, -0.245, 0.35), WARMWHITE,
    chamfer=False)

export("SM_LB_Assembly_HVACModule_v001", "AssemblyShop/HVACModule_v001")
preview("SM_LB_Assembly_HVACModule_v001", "AssemblyShop/HVACModule_v001")
