"""Assembly door-line carrier: hangs one door from the overhead track.

Recognised by its single trolley (it rides the existing 4 m track segments,
rail at 3.9 m), the drop tube, and the padded hook frame gripping a door by
its window aperture, with a lower guide pad against the skin.
"""
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, STEEL, WARMWHITE, box, cyl, export,
                          preview, reset)

reset()

RAIL_Z = 3.92

box("TrolleyBody", (0.40, 0.30, 0.14), (0, 0, RAIL_Z + 0.10), CHARCOAL)
for wx in (-0.12, 0.12):
    for sy in (-0.17, 0.17):
        cyl("TrolleyWheel", 0.06, 0.045, (wx, sy, RAIL_Z), STEEL, axis="Y",
            verts=12)
box("DropLug", (0.16, 0.12, 0.14), (0, 0, RAIL_Z - 0.04), CHARCOAL)
box("DropTube", (0.08, 0.08, 1.30), (0, 0, RAIL_Z - 0.74), GREEN)

# Hook frame: cross bar, two padded hooks, lower guide pad.
box("CrossBar", (0.95, 0.09, 0.09), (0, 0, RAIL_Z - 1.42), GREEN)
for hx in (-0.40, 0.40):
    box("HookDrop", (0.06, 0.06, 0.30), (hx, 0, RAIL_Z - 1.60), STEEL)
    box("HookTip", (0.06, 0.16, 0.05), (hx, 0.06, RAIL_Z - 1.76), STEEL)
    box("HookPad", (0.08, 0.03, 0.08), (hx, 0.10, RAIL_Z - 1.72), CHARCOAL,
        chamfer=False)
box("GuideArm", (0.06, 0.06, 0.95), (0, 0.02, RAIL_Z - 1.90), GREEN)
box("GuidePad", (0.20, 0.04, 0.14), (0, 0.08, RAIL_Z - 2.36), CHARCOAL)
box("IDTag", (0.10, 0.02, 0.07), (0.30, -0.05, RAIL_Z - 1.42), WARMWHITE,
    chamfer=False)

export("SM_LB_Assembly_DoorCarrier_v001", "AssemblyShop/DoorCarrier_v001")
preview("SM_LB_Assembly_DoorCarrier_v001", "AssemblyShop/DoorCarrier_v001")
