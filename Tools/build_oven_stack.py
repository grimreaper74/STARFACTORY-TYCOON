"""Paint oven exhaust stack: the tall flue rising off the oven burner row.

Recognised by its plinth, the tapering two-stage stack with band clamps,
the guy ring with three stays, the access ladder with hoops, and the
weather cap. The tallest paint-shop landmark.
"""
import math
import sys

import bpy

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
import lb_model_kit as kit
from lb_model_kit import (CHARCOAL, GREEN, STEEL, WARMWHITE, box, cyl, export,
                          preview, reset)

reset()

box("Plinth", (1.4, 1.4, 0.3), (0, 0, 0.15), CHARCOAL)
cyl("StackLower", 0.38, 4.0, (0, 0, 2.3), GREEN, verts=22)
cyl("StackUpper", 0.30, 3.6, (0, 0, 6.1), GREEN, verts=22)
cyl("StackJoint", 0.42, 0.15, (0, 0, 4.35), CHARCOAL, verts=22)
for bz in (1.4, 3.2, 5.4, 7.0):
    cyl("Band", 0.415 if bz < 4.3 else 0.335, 0.08, (0, 0, bz), CHARCOAL,
        verts=22)
cyl("WeatherCap", 0.44, 0.10, (0, 0, 8.0), CHARCOAL, verts=22)
cyl("CapCone", 0.20, 0.25, (0, 0, 8.15), GREEN, verts=18)

# Guy ring with three stays run ring-to-anchor so the ends land on hardware.
# Oriented with a track quaternion: hand-rolled eulers tilted the stays the
# wrong way and left both ends in mid-air.
import mathutils

cyl("GuyRing", 0.36, 0.10, (0, 0, 5.6), STEEL, verts=22)
for n in range(3):
    a = n * 2.0944 + 0.5
    ca, sa = math.cos(a), math.sin(a)
    top = mathutils.Vector((ca * 0.34, sa * 0.34, 5.62))
    foot = mathutils.Vector((ca * 2.0, sa * 2.0, 0.15))
    run = foot - top
    rot = run.to_track_quat("Z", "Y").to_euler()
    mid = (top + foot) * 0.5
    box("GuyStay", (0.035, 0.035, run.length + 0.15), tuple(mid), STEEL,
        rot=(rot.x, rot.y, rot.z), chamfer=False)
    box("GuyAnchor", (0.3, 0.3, 0.22), (ca * 2.0, sa * 2.0, 0.11), CHARCOAL)

# Access ladder with cage hoops up the south face.
for rz in range(14):
    box("Rung", (0.28, 0.02, 0.02), (0, -0.44, 0.6 + rz * 0.5), STEEL,
        chamfer=False)
for rx in (-0.14, 0.14):
    box("LadderRail", (0.03, 0.03, 7.0), (rx, -0.44, 4.1), STEEL,
        chamfer=False)
for hz in (2.6, 4.1, 5.6):
    bpy.ops.mesh.primitive_torus_add(major_radius=0.30, minor_radius=0.022,
                                     location=(0, -0.70, hz),
                                     major_segments=20, minor_segments=8)
    hoop = bpy.context.active_object
    hoop.name = "CageHoop"
    hoop.data.materials.append(kit.material(*STEEL))
box("IDPlate", (0.24, 0.02, 0.12), (0, -0.72, 1.2), WARMWHITE, chamfer=False)

export("SM_LB_Paint_OvenStack_v001", "PaintShop/OvenStack_v001")
preview("SM_LB_Paint_OvenStack_v001", "PaintShop/OvenStack_v001", distance=20.0)
