"""Weld shop pedestal spot welder. Eight or more per shop, so detail here repeats widely.

A pedestal welder is recognised by its throat: two arms reaching forward from a
transformer body, electrodes facing each other across the gap, an air cylinder above
driving the upper arm, and water hoses looping back to the cooler.
"""
import math
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, RED, STEEL, WARMWHITE, YELLOW, box,
                          column, cyl, export, preview, reset)

reset()

# Bolted base and the fabricated column that carries the transformer.
box("Base", (0.86, 0.86, 0.18), (0, 0, 0.09), CHARCOAL)
box("BaseSkirt", (0.94, 0.94, 0.05), (0, 0, 0.03), YELLOW)
column("Body", (0, 0, 0.18), 1.1, GREEN, width=0.34)

# Transformer body with cooling fins and a nameplate.
box("Transformer", (0.64, 0.52, 0.54), (0, -0.1, 1.62), GREEN)
for n in range(6):
    box("TxFin", (0.66, 0.02, 0.44), (0, -0.36 + n * 0.03, 1.62), CHARCOAL,
        chamfer=False)
box("TxPlate", (0.2, 0.02, 0.1), (0.2, -0.37, 1.75), WARMWHITE, chamfer=False)

# The throat: upper and lower arms with holders and electrode caps.
for z, tag in ((1.94, "Upper"), (1.4, "Lower")):
    box("Arm" + tag, (0.92, 0.15, 0.13), (0.4, 0, z), STEEL)
    box("ArmRib" + tag, (0.72, 0.05, 0.07), (0.34, 0, z + 0.09), CHARCOAL,
        chamfer=False)
    box("Holder" + tag, (0.16, 0.17, 0.17), (0.83, 0, z), CHARCOAL)
cyl("ElectrodeUpper", 0.032, 0.22, (0.83, 0, 1.81), STEEL)
cyl("CapUpper", 0.026, 0.07, (0.83, 0, 1.7), RED)
cyl("ElectrodeLower", 0.032, 0.22, (0.83, 0, 1.53), STEEL)
cyl("CapLower", 0.026, 0.07, (0.83, 0, 1.64), STEEL)

# Air cylinder above, driving the upper arm through a clevis.
cyl("Cylinder", 0.095, 0.46, (0.06, 0, 2.2), CHARCOAL)
cyl("CylRod", 0.028, 0.24, (0.06, 0, 1.94), STEEL)
box("Clevis", (0.12, 0.14, 0.1), (0.06, 0, 1.86), STEEL)
cyl("AirLine", 0.018, 0.5, (-0.14, 0.1, 2.1), STEEL)

# Water cooling: two hoses looping to the manifold on the column.
box("Manifold", (0.16, 0.12, 0.22), (-0.24, 0.16, 1.5), GREEN)
for sy in (0.0, 0.07):
    cyl("WaterHose", 0.022, 0.62, (-0.06, 0.14 + sy, 1.66), STEEL, axis="X")

# Weld controller with an isolator and an e-stop.
box("Controller", (0.32, 0.28, 0.54), (-0.5, 0, 0.47), GREEN)
box("CtrlDoor", (0.02, 0.24, 0.44), (-0.66, 0, 0.5), CHARCOAL, chamfer=False)
cyl("Isolator", 0.035, 0.06, (-0.66, 0.07, 0.66), YELLOW, axis="X")
cyl("EStop", 0.055, 0.06, (-0.66, -0.07, 0.66), RED, axis="X")

export("SM_LB_Weld_PedestalWelder_v001", "WeldShop/PedestalWelder_v001")
preview("SM_LB_Weld_PedestalWelder_v001", "WeldShop/PedestalWelder_v001")
