"""Assembly chassis hanger: the H-frame carrier that rides the overhead track.

Recognised by its two wheeled trolleys straddling the monorail flange, the
drop tubes, and the low cradle beams with four sill pads the body sits on.
Floor pivot with the geometry at height, so it places at Z=0 under the track.
"""
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, STEEL, WARMWHITE, box, cyl, export,
                          preview, reset)

reset()

# Trolleys straddling the rail's bottom flange (flange top at 3.80).
for tx in (-0.95, 0.95):
    box("TrolleyBody", (0.46, 0.36, 0.14), (tx, 0, 4.01), CHARCOAL)
    for wx in (-0.14, 0.14):
        for sy in (-0.19, 0.19):
            cyl("TrolleyWheel", 0.07, 0.05, (tx + wx, sy, 3.87), STEEL,
                axis="Y", verts=14)
    box("DropLug", (0.20, 0.14, 0.20), (tx, 0, 3.82), CHARCOAL)

# Spine and drop tubes.
box("Spine", (2.20, 0.13, 0.13), (0, 0, 3.66), GREEN)
for tx in (-0.95, 0.95):
    box("DropTube", (0.10, 0.10, 1.60), (tx, 0, 2.86), GREEN)
    # Stay runs from the spine (0.55, 3.60) to the drop tube (0.95, 2.95).
    sign = 1.0 if tx > 0 else -1.0
    box("Stay", (0.76, 0.05, 0.06), (sign * 0.75, 0, 3.27), CHARCOAL,
        rot=(0.0, sign * 1.02, 0.0))

# Cradle beams with four sill pads and upstand hooks.
for tx in (-0.95, 0.95):
    box("CradleBeam", (0.11, 1.55, 0.11), (tx, 0, 2.06), GREEN)
    for sy in (-0.70, 0.70):
        box("SillPad", (0.24, 0.12, 0.05), (tx, sy, 2.14), STEEL)
        box("SillHook", (0.24, 0.04, 0.16), (tx, sy + (0.07 if sy > 0
            else -0.07), 2.19), CHARCOAL, chamfer=False)
box("IDPlate", (0.02, 0.20, 0.12), (1.06, 0, 2.86), WARMWHITE, chamfer=False)

export("SM_LB_Assembly_ChassisHanger_v001", "AssemblyShop/ChassisHanger_v001")
preview("SM_LB_Assembly_ChassisHanger_v001", "AssemblyShop/ChassisHanger_v001")
