"""Weld stud feeder: the P15 vibratory-bowl feeder with its hose run.

Recognised by the legged cabinet, the steel vibratory bowl with rim ring
and centre cone, the front panel with gauge and buttons, and the hose
bundle arcing out to a delivery stand with a stud-gun holster.
"""
import sys

import bpy

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
import lb_model_kit as kit
from lb_model_kit import (CHARCOAL, GREEN, STEEL, WARMWHITE, box, cyl, export,
                          preview, reset)

reset()

for lx in (-0.32, 0.32):
    for ly in (-0.2, 0.2):
        box("Leg", (0.06, 0.06, 0.24), (lx, ly, 0.12), CHARCOAL,
            chamfer=False)
box("Cabinet", (0.75, 0.55, 0.9), (0, 0, 0.69), GREEN)
box("CabinetTop", (0.8, 0.6, 0.06), (0, 0, 1.17), CHARCOAL)

# Vibratory bowl with rim ring and centre cone.
cyl("BowlBase", 0.12, 0.12, (0, 0, 1.26), CHARCOAL, verts=14)
cyl("Bowl", 0.30, 0.26, (0, 0, 1.45), STEEL, verts=22)
bpy.ops.mesh.primitive_torus_add(major_radius=0.30, minor_radius=0.025,
                                 location=(0, 0, 1.58), major_segments=22,
                                 minor_segments=8)
rim = bpy.context.active_object
rim.name = "BowlRim"
rim.data.materials.append(kit.material(*STEEL))
cyl("BowlCone", 0.1, 0.14, (0, 0, 1.62), CHARCOAL, verts=14)

# Front panel with gauge and buttons.
box("Panel", (0.5, 0.03, 0.34), (0, -0.29, 0.85), WARMWHITE, chamfer=False)
cyl("Gauge", 0.06, 0.04, (-0.13, -0.31, 0.92), CHARCOAL, axis="Y", verts=14)
for n in range(3):
    cyl("Button", 0.02, 0.03, (0.06 + n * 0.09, -0.31, 0.78), CHARCOAL,
        axis="Y", verts=8)

# Hose bundle out the east side, down and along to the delivery stand.
for m, hy in enumerate((-0.1, 0.0, 0.1)):
    cyl("HoseOut", 0.025, 0.55, (0.62, hy, 1.0 - m * 0.01), CHARCOAL,
        axis="X", verts=8)
    cyl("HoseElbow", 0.05, 0.08, (0.9, hy, 0.96), CHARCOAL, verts=8)
    cyl("HoseDrop", 0.025, 0.85, (0.9, hy, 0.52), CHARCOAL, verts=8)
    cyl("HoseRun", 0.025, 0.6, (1.2, hy, 0.12), CHARCOAL, axis="X", verts=8)
box("StandBase", (0.3, 0.3, 0.05), (1.55, 0, 0.03), CHARCOAL)
box("StandPost", (0.07, 0.07, 0.9), (1.55, 0, 0.5), GREEN)
box("Holster", (0.12, 0.14, 0.22), (1.62, 0, 0.9), STEEL)
cyl("GunBody", 0.035, 0.2, (1.62, 0, 1.08), CHARCOAL, verts=10)
box("IDPlate", (0.2, 0.02, 0.1), (0, -0.31, 0.58), WARMWHITE, chamfer=False)

export("SM_LB_Weld_StudFeeder_v001", "WeldShop/StudFeeder_v001")
preview("SM_LB_Weld_StudFeeder_v001", "WeldShop/StudFeeder_v001")
