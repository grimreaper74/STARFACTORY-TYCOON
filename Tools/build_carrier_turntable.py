"""Paint carrier turntable: the skid turntable at the serpentine fold.

Recognised by the ringed plinth with its yellow guard band, the rotating
platform carrying two skid rails with end stops, the centre bearing hub,
the rim drive unit, and the control post.
"""
import sys

import bpy

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
import lb_model_kit as kit
from lb_model_kit import (CHARCOAL, GREEN, STEEL, WARMWHITE, YELLOW, box, cyl,
                          export, preview, reset)

reset()

cyl("Plinth", 1.7, 0.15, (0, 0, 0.075), CHARCOAL, verts=36)
bpy.ops.mesh.primitive_torus_add(major_radius=1.68, minor_radius=0.03,
                                 location=(0, 0, 0.16), major_segments=36,
                                 minor_segments=8)
band = bpy.context.active_object
band.name = "GuardBand"
band.data.materials.append(kit.material(*YELLOW))
cyl("Platform", 1.5, 0.14, (0, 0, 0.29), GREEN, verts=36)
cyl("Hub", 0.18, 0.1, (0, 0, 0.41), CHARCOAL, verts=16)

# Skid rails with end stops.
for ry in (-0.5, 0.5):
    box("SkidRail", (2.6, 0.18, 0.12), (0, ry, 0.42), STEEL)
    for ex in (-1.26, 1.26):
        box("RailStop", (0.08, 0.18, 0.2), (ex, ry, 0.46), CHARCOAL)

# Rim drive unit and control post.
box("DriveBox", (0.5, 0.42, 0.45), (1.95, 0, 0.24), GREEN)
cyl("DriveMotor", 0.12, 0.4, (2.3, 0, 0.3), STEEL, axis="X", verts=12)
box("Pinion", (0.2, 0.3, 0.2), (1.66, 0, 0.2), CHARCOAL)
box("Placard", (0.02, 0.24, 0.14), (2.21, 0, 0.55), WARMWHITE,
    chamfer=False)
box("PostBase", (0.24, 0.24, 0.05), (-1.95, 0.7, 0.03), CHARCOAL)
box("Post", (0.08, 0.08, 1.0), (-1.95, 0.7, 0.55), GREEN)
box("PostPanel", (0.26, 0.06, 0.2), (-1.95, 0.67, 1.12), WARMWHITE)

export("SM_LB_Paint_CarrierTurntable_v001", "PaintShop/CarrierTurntable_v001")
preview("SM_LB_Paint_CarrierTurntable_v001", "PaintShop/CarrierTurntable_v001")
