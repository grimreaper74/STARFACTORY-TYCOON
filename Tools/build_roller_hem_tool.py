"""Weld roller-hem robot tool: the end effector that rolls closure hems.

Palette-native M_LB_BS_* slot names so ALBBodyShopRobotActor can carry
it. Recognised by the mount flange, the forked head, and the two
staggered hem rollers with a sprung pre-roller.
"""
import math
import sys

import bpy

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
import lb_model_kit as kit
from lb_model_kit import box, cyl, export, preview, reset

reset()

# Robot palette slots, not the kit MAT_* names.
EMERALD = ("M_LB_BS_EmeraldPanel", (0.047, 0.153, 0.137, 1.0))
GRAPHITE = ("M_LB_BS_GraphiteTooling", (0.055, 0.063, 0.071, 1.0))
BRUSHED = ("M_LB_BS_BrushedSteel", (0.44, 0.46, 0.48, 1.0))
CREAM = ("M_LB_BS_CreamPaint", (0.88, 0.86, 0.80, 1.0))

cyl("MountFlange", 0.09, 0.04, (0, 0, 0.02), BRUSHED, verts=16)
for n in range(4):
    a = n * math.pi / 2 + 0.4
    cyl("FlangeBolt", 0.012, 0.03, (math.cos(a) * 0.065,
        math.sin(a) * 0.065, 0.035), GRAPHITE, verts=8)
box("Body", (0.14, 0.12, 0.16), (0, 0, 0.13), EMERALD)
box("ForkArm", (0.05, 0.1, 0.14), (-0.06, 0, 0.27), GRAPHITE)
box("ForkArm2", (0.05, 0.1, 0.1), (0.07, 0, 0.25), GRAPHITE)

# Main hem roller between the fork tips.
cyl("HemRoller", 0.045, 0.1, (0.0, 0, 0.35), BRUSHED, axis="X", verts=16)
cyl("RollerAxle", 0.015, 0.17, (0.005, 0, 0.35), GRAPHITE, axis="X",
    verts=8)
# Sprung pre-roller ahead of it.
box("SpringHousing", (0.04, 0.04, 0.08), (0.1, 0, 0.33), EMERALD)
cyl("PreRoller", 0.028, 0.06, (0.1, 0, 0.4), BRUSHED, axis="X", verts=12)
box("IDBand", (0.02, 0.06, 0.03), (-0.08, 0, 0.13), CREAM, chamfer=False)

export("SM_LB_Weld_RollerHemTool_v001", "WeldShop/RollerHemTool_v001")
preview("SM_LB_Weld_RollerHemTool_v001", "WeldShop/RollerHemTool_v001")
