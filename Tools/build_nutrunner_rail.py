"""Assembly nutrunner reaction rail: 8 m of hanging DC torque tools.

Recognised by the long rail with sliding balancer units, each dropping a
coiled service line to a DC nutrunner with a torque reaction arm. Four tool
positions along the rail; end columns carry the controller and beacon.
"""
import math
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, RED, STEEL, WARMWHITE, YELLOW, box,
                          column, cyl, export, preview, reset)

reset()

for cx in (-3.9, 3.9):
    column("Post", (cx, 0, 0), 2.75, GREEN, width=0.28)
box("Rail", (8.0, 0.14, 0.20), (0, 0, 3.00), GREEN)
box("RailRib", (8.0, 0.06, 0.06), (0, 0, 3.14), CHARCOAL, chamfer=False)

import bpy
from lb_model_kit import material
for n, tx in enumerate((-2.7, -0.9, 0.9, 2.7)):
    # Slider and balancer body.
    box("Slider", (0.30, 0.22, 0.14), (tx, 0, 2.90), CHARCOAL)
    cyl("Balancer", 0.10, 0.30, (tx, 0, 2.68), CHARCOAL, verts=14)
    cyl("BalancerHook", 0.02, 0.14, (tx, 0, 2.48), STEEL, verts=8)
    # Coiled service line: a stack of small tori reads as the coil.
    for c in range(4):
        bpy.ops.mesh.primitive_torus_add(
            location=(tx, 0, 2.30 - c * 0.09), rotation=(0.0, 0.0, 0.0),
            major_radius=0.07, minor_radius=0.014,
            major_segments=16, minor_segments=6)
        coil = bpy.context.active_object
        coil.name = "Coil"
        coil.data.materials.append(material(*CHARCOAL))
    cyl("Line", 0.012, 0.55, (tx, 0, 1.68), CHARCOAL, verts=8)
    # The nutrunner: body, grip, steel output bit.
    cyl("ToolBody", 0.045, 0.30, (tx, 0, 1.32), GREEN, verts=12)
    box("ToolGrip", (0.07, 0.07, 0.16), (tx, 0.05, 1.24), CHARCOAL)
    cyl("ToolBit", 0.018, 0.14, (tx, 0, 1.12), STEEL, verts=8)
    # Torque reaction arm from the rail to the tool: two links.
    box("ReactUpper", (0.55, 0.05, 0.06), (tx + 0.26, 0.10, 2.35), STEEL,
        rot=(0.0, 0.75, 0.0))
    box("ReactLower", (0.55, 0.05, 0.06), (tx + 0.26, 0.10, 1.75), STEEL,
        rot=(0.0, -0.75, 0.0))
    cyl("ReactKnee", 0.045, 0.07, (tx + 0.47, 0.10, 2.05), CHARCOAL,
        axis="Y", verts=10)

box("Controller", (0.42, 0.30, 0.70), (3.92, -0.42, 0.35), GREEN)
box("CtrlDoor", (0.02, 0.26, 0.60), (3.70, -0.42, 0.35), CHARCOAL,
    chamfer=False)
cyl("Beacon", 0.04, 0.09, (3.9, 0, 3.20), RED)
box("FloorMark", (7.6, 0.05, 0.006), (0, 0.65, 0.003), YELLOW, chamfer=False)

export("SM_LB_Assembly_NutrunnerReactionRail_v001",
       "AssemblyShop/NutrunnerRail_v001")
preview("SM_LB_Assembly_NutrunnerReactionRail_v001",
        "AssemblyShop/NutrunnerRail_v001")
