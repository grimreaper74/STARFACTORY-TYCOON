"""Paint sealer robot nozzle: the bead applicator end effector.

Palette-native M_LB_BS_* slot names so ALBBodyShopRobotActor can carry
it. Recognised by the mount flange, the angled applicator barrel with
its tapering nozzle, the material hose stub, and the bead guide wheel.
"""
import math
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
import lb_model_kit as kit
from lb_model_kit import box, cyl, export, preview, reset

reset()

EMERALD = ("M_LB_BS_EmeraldPanel", (0.047, 0.153, 0.137, 1.0))
GRAPHITE = ("M_LB_BS_GraphiteTooling", (0.055, 0.063, 0.071, 1.0))
BRUSHED = ("M_LB_BS_BrushedSteel", (0.44, 0.46, 0.48, 1.0))
CREAM = ("M_LB_BS_CreamPaint", (0.88, 0.86, 0.80, 1.0))

cyl("MountFlange", 0.09, 0.04, (0, 0, 0.02), BRUSHED, verts=16)
for n in range(4):
    a = n * math.pi / 2 + 0.4
    cyl("FlangeBolt", 0.012, 0.03, (math.cos(a) * 0.065,
        math.sin(a) * 0.065, 0.035), GRAPHITE, verts=8)
box("Body", (0.13, 0.11, 0.14), (0, 0, 0.12), EMERALD)
cyl("HoseStub", 0.03, 0.1, (0, 0.08, 0.16), GRAPHITE, axis="Y", verts=10)
cyl("HoseElbow", 0.045, 0.06, (0, 0.14, 0.16), GRAPHITE, axis="Y", verts=10)

# Angled applicator barrel with tapering nozzle stages.
barrel_rot = (0.0, math.radians(25.0), 0.0)
cyl_o = box("BarrelMount", (0.08, 0.08, 0.06), (0.02, 0, 0.21), GRAPHITE)
obj = cyl("Barrel", 0.035, 0.22, (0.07, 0, 0.3), BRUSHED, verts=12)
obj.rotation_euler = barrel_rot
import bpy
bpy.context.view_layer.objects.active = obj
bpy.ops.object.transform_apply(rotation=True)
obj2 = cyl("NozzleTaper", 0.02, 0.08, (0.13, 0, 0.42), GRAPHITE, verts=10)
obj2.rotation_euler = barrel_rot
bpy.context.view_layer.objects.active = obj2
bpy.ops.object.transform_apply(rotation=True)
obj3 = cyl("NozzleTip", 0.008, 0.05, (0.155, 0, 0.47), BRUSHED, verts=8)
obj3.rotation_euler = barrel_rot
bpy.context.view_layer.objects.active = obj3
bpy.ops.object.transform_apply(rotation=True)

# Bead guide wheel ahead of the tip, clamped off the barrel.
box("GuideBracket", (0.16, 0.03, 0.03), (0.12, 0, 0.36), GRAPHITE,
    chamfer=False)
box("GuideArm", (0.03, 0.03, 0.1), (0.19, 0, 0.4), EMERALD, chamfer=False)
cyl("GuideWheel", 0.025, 0.02, (0.19, 0, 0.46), BRUSHED, axis="Y", verts=12)
box("IDBand", (0.02, 0.05, 0.03), (-0.07, 0, 0.12), CREAM, chamfer=False)

export("SM_LB_Paint_SealerNozzleTool_v001", "PaintShop/SealerNozzleTool_v001")
preview("SM_LB_Paint_SealerNozzleTool_v001", "PaintShop/SealerNozzleTool_v001")
