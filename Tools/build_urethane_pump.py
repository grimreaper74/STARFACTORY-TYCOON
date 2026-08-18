"""Assembly urethane melt and pump unit feeding the glazing robots.

Recognised by the drum on its tray, the two-post ram with crosshead and
follower plate pressing into the drum, the pump block on the crosshead, the
heated hose looping to a boom, and the temperature control cabinet.
"""
import math
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, RED, STEEL, WARMWHITE, YELLOW, box,
                          cyl, export, preview, reset)

reset()

# Drum tray, drum, and the two-post ram over it.
box("Tray", (1.30, 1.00, 0.08), (0, 0, 0.04), CHARCOAL)
cyl("Drum", 0.30, 0.90, (0, 0, 0.53), STEEL, verts=22)
cyl("DrumRib", 0.31, 0.03, (0, 0, 0.75), CHARCOAL, verts=22)
for px in (-0.52, 0.52):
    cyl("RamPost", 0.055, 2.10, (px, 0, 1.13), STEEL, verts=14)
    box("PostFoot", (0.22, 0.22, 0.05), (px, 0, 0.10), CHARCOAL)
box("Crosshead", (1.30, 0.34, 0.24), (0, 0, 2.05), GREEN)
cyl("FollowerRod", 0.075, 0.75, (0, 0, 1.55), STEEL, verts=14)
cyl("FollowerPlate", 0.285, 0.10, (0, 0, 1.03), CHARCOAL, verts=22)
box("PumpBlock", (0.34, 0.28, 0.36), (0, 0, 2.30), CHARCOAL)
cyl("PumpMotor", 0.11, 0.30, (0.30, 0, 2.30), GREEN, axis="X", verts=14)

# Heated hose looping from the pump to the boom outlet.
import bpy
from lb_model_kit import material
bpy.ops.mesh.primitive_torus_add(location=(0.42, 0, 2.62),
    rotation=(0.0, 1.5708, 0.0), major_radius=0.28, minor_radius=0.035,
    major_segments=20, minor_segments=8)
loop = bpy.context.active_object
loop.name = "HoseLoop"
loop.data.materials.append(material(*CHARCOAL))
box("Boom", (1.5, 0.10, 0.10), (0.9, 0, 2.85), GREEN)
cyl("BoomPost", 0.045, 0.40, (1.6, 0, 2.60), STEEL, verts=12)
cyl("HoseDrop", 0.035, 1.1, (1.6, 0, 1.95), CHARCOAL, verts=12)
box("HoseHead", (0.10, 0.10, 0.20), (1.6, 0, 1.32), STEEL)

# Temperature control cabinet with zone lamps.
box("Cabinet", (0.55, 0.40, 1.20), (-1.15, 0, 0.60), GREEN)
box("CabDoor", (0.02, 0.34, 1.05), (-1.43, 0, 0.60), CHARCOAL, chamfer=False)
for n in range(3):
    cyl("ZoneLamp", 0.025, 0.03, (-1.44, -0.10 + n * 0.10, 1.02), WARMWHITE,
        axis="X", verts=10)
cyl("CabEStop", 0.04, 0.05, (-1.44, 0, 0.75), RED, axis="X")
cyl("Isolator", 0.028, 0.05, (-1.44, 0.12, 0.75), YELLOW, axis="X")
box("IDPlate", (0.02, 0.18, 0.09), (-1.44, 0, 1.12), WARMWHITE, chamfer=False)
cyl("CabConduit", 0.02, 0.7, (-1.15, 0.15, 1.55), STEEL, verts=10)

export("SM_LB_Assembly_UrethanePumpUnit_v001", "AssemblyShop/UrethanePump_v001")
preview("SM_LB_Assembly_UrethanePumpUnit_v001", "AssemblyShop/UrethanePump_v001")
