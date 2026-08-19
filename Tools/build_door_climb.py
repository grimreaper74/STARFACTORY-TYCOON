"""Assembly door conveyor climb section: floor level up to the door line.

Recognised by its two goalposts of different heights carrying an inclined
I-beam rail, the chain cover following the slope, and the kick gussets at
both transitions. Chains with the flat overhead track segments at the top
(rail 3.9 m) and reaches down to a 2.0 m pickup at the low end.
"""
import math
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, STEEL, WARMWHITE, box, column, cyl,
                          export, preview, reset)

reset()

LOW_Z, HIGH_Z = 2.0, 3.9
LENGTH = 4.0
ANGLE = math.atan2(HIGH_Z - LOW_Z, LENGTH)

column("PostLow", (-LENGTH * 0.5, 0, 0), LOW_Z + 0.25, GREEN, width=0.28)
column("PostHigh", (LENGTH * 0.5, 0, 0), HIGH_Z + 0.25, GREEN, width=0.28)

# Inclined rail: I-beam profile along the slope with the chain cover above.
MID_Z = (LOW_Z + HIGH_Z) * 0.5
RAIL_LEN = math.hypot(LENGTH, HIGH_Z - LOW_Z)
box("RailTopFlange", (RAIL_LEN, 0.22, 0.04), (0, 0, MID_Z + 0.14), CHARCOAL,
    rot=(0.0, -ANGLE, 0.0), chamfer=False)
box("RailWeb", (RAIL_LEN, 0.08, 0.24), (0, 0, MID_Z), CHARCOAL,
    rot=(0.0, -ANGLE, 0.0))
box("RailBottomFlange", (RAIL_LEN, 0.26, 0.05), (0, 0, MID_Z - 0.14), STEEL,
    rot=(0.0, -ANGLE, 0.0))
box("ChainCover", (RAIL_LEN, 0.18, 0.10), (0, 0, MID_Z + 0.24), GREEN,
    rot=(0.0, -ANGLE, 0.0))

# Transition gussets tie the rail ends to the post caps.
box("GussetLow", (0.45, 0.14, 0.30), (-LENGTH * 0.5 + 0.2, 0, LOW_Z + 0.14),
    CHARCOAL)
box("GussetHigh", (0.45, 0.14, 0.30), (LENGTH * 0.5 - 0.2, 0, HIGH_Z + 0.14),
    CHARCOAL)

# Anti-runback pawl housing mid-slope and the drive at the crest.
box("PawlBox", (0.30, 0.24, 0.20), (0, 0, MID_Z + 0.42), CHARCOAL)
box("DriveBox", (0.5, 0.42, 0.35), (LENGTH * 0.5, 0, HIGH_Z + 0.55), GREEN)
cyl("DriveMotor", 0.10, 0.28, (LENGTH * 0.5, 0.32, HIGH_Z + 0.55), CHARCOAL,
    axis="Y", verts=14)
box("IDPlate", (0.02, 0.2, 0.11), (-LENGTH * 0.5 - 0.15, 0, 1.4), WARMWHITE,
    chamfer=False)

export("SM_LB_Assembly_DoorClimbSection_v001", "AssemblyShop/DoorClimb_v001")
preview("SM_LB_Assembly_DoorClimbSection_v001", "AssemblyShop/DoorClimb_v001")
