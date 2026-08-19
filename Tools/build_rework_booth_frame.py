"""Weld rework booth frame: the P17 curtained bay with local extraction.

Recognised by the three-sided panelled frame with an open curtained front,
the tapering extraction hood with its vertical duct and roof fan set, and
the task light bar under the hood. Open front faces south.
"""
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, STEEL, WARMWHITE, box, column, cyl,
                          export, preview, reset)

reset()

box("FloorPlate", (4.0, 3.2, 0.06), (0, 0, 0.03), CHARCOAL)
for px in (-1.9, 1.9):
    for py in (-1.5, 1.5):
        box("Post", (0.15, 0.15, 3.0), (px, py, 1.56), GREEN)
        box("PostCap", (0.2, 0.2, 0.05), (px, py, 3.08), CHARCOAL)
# Header ring.
box("HeaderF", (3.95, 0.12, 0.18), (0, -1.5, 2.97), GREEN)
box("HeaderB", (3.95, 0.12, 0.18), (0, 1.5, 2.97), GREEN)
for px in (-1.9, 1.9):
    box("HeaderS", (0.12, 3.15, 0.18), (px, 0, 2.97), GREEN)

# Panelled sides and back below the open upper band.
box("BackPanel", (3.8, 0.05, 1.5), (0, 1.48, 0.81), STEEL)
box("BackRail", (3.8, 0.07, 0.07), (0, 1.48, 1.6), CHARCOAL)
for px in (-1.88, 1.88):
    box("SidePanel", (0.05, 3.0, 1.5), (px, 0, 0.81), STEEL)
    box("SideRail", (0.07, 3.0, 0.07), (px, 0, 1.6), CHARCOAL)

# Extraction hood engaging the header plane, fan set seated on the corner
# post, and the transfer duct run exactly between them.
import bpy
import mathutils

import lb_model_kit as kit

box("HoodMouth", (2.2, 1.8, 0.3), (0, 0.2, 2.95), CHARCOAL)
box("HoodMid", (1.5, 1.2, 0.3), (0, 0.2, 3.25), CHARCOAL)
box("HoodTop", (0.9, 0.7, 0.3), (0, 0.2, 3.55), CHARCOAL)
cyl("Duct", 0.18, 0.6, (0, 0.2, 4.0), STEEL, verts=14)
cyl("DuctElbow", 0.20, 0.14, (0, 0.2, 4.32), CHARCOAL, verts=14)
box("FanBox", (0.6, 0.5, 0.45), (1.9, 1.5, 3.33), GREEN)
cyl("FanOutlet", 0.12, 0.4, (1.9, 1.5, 3.7), STEEL, verts=12)
start = mathutils.Vector((0.0, 0.2, 4.25))
end = mathutils.Vector((1.9, 1.5, 3.5))
run = end - start
duct = cyl("TransferDuct", 0.12, run.length + 0.1,
           tuple((start + end) * 0.5), STEEL, verts=12)
duct.rotation_euler = run.to_track_quat("Z", "Y").to_euler()
bpy.context.view_layer.objects.active = duct
bpy.ops.object.transform_apply(rotation=True)

# Task light bar under the hood.
box("LightBar", (1.8, 0.12, 0.06), (0, -0.6, 2.77), WARMWHITE, chamfer=False)

# Curtain rail and strips across the open front.
box("CurtainRail", (3.6, 0.05, 0.05), (0, -1.5, 2.85), STEEL)
for n in range(6):
    sx = -1.25 + n * 0.5
    drop = 1.05 if n % 2 == 0 else 1.25
    box("Curtain", (0.4, 0.03, drop), (sx, -1.5, 2.82 - drop / 2), CHARCOAL,
        chamfer=False)
box("Placard", (0.3, 0.02, 0.18), (-1.9, -1.59, 2.2), WARMWHITE,
    chamfer=False)

export("SM_LB_Weld_ReworkBoothFrame_v001", "WeldShop/ReworkBoothFrame_v001")
preview("SM_LB_Weld_ReworkBoothFrame_v001", "WeldShop/ReworkBoothFrame_v001")
