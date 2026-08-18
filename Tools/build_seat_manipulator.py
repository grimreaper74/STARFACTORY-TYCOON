"""Assembly seat install manipulator: rail-mounted zero-gravity seat loader.

Recognised by its overhead rail on two columns, the trolley with a hanging
mast and balance cylinder, the articulated forearm ending in a cradle gripper
holding a seat, and the staged seats waiting beside a column. Lights-out
plant: the manipulator is servo-driven, so no operator grips are modelled.
"""
import math
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, RED, STEEL, WARMWHITE, YELLOW, box,
                          column, cyl, export, preview, reset)

reset()


def seat(prefix, x, y, z, yaw=0.0):
    c, s = math.cos(yaw), math.sin(yaw)
    box(prefix + "Cushion", (0.46, 0.46, 0.12), (x, y, z + 0.06), CHARCOAL)
    box(prefix + "Back", (0.10, 0.46, 0.58),
        (x - 0.20 * c, y - 0.20 * s, z + 0.38), CHARCOAL,
        rot=(0.0, -0.20, yaw))
    box(prefix + "Head", (0.08, 0.24, 0.14),
        (x - 0.30 * c, y - 0.30 * s, z + 0.72), CHARCOAL)
    box(prefix + "Frame", (0.40, 0.40, 0.05), (x, y, z - 0.03), STEEL,
        chamfer=False)


# Columns and rail.
for cx in (-1.8, 1.8):
    column("Post", (cx, 0, 0), 2.80, GREEN, width=0.26)
box("Rail", (3.9, 0.16, 0.22), (0, 0, 3.06), GREEN)
box("RailStop", (0.06, 0.20, 0.28), (1.92, 0, 3.06), CHARCOAL, chamfer=False)

# Trolley, mast, balance cylinder.
box("Trolley", (0.44, 0.30, 0.16), (0.5, 0, 2.92), CHARCOAL)
for wx in (-0.13, 0.13):
    cyl("TrolleyWheel", 0.06, 0.05, (0.5 + wx, 0.14, 3.00), STEEL, axis="Y",
        verts=12)
cyl("Mast", 0.05, 1.35, (0.5, 0, 2.18), STEEL)
cyl("BalanceCyl", 0.065, 0.75, (0.64, 0.10, 2.40), CHARCOAL, verts=14)
cyl("BalanceRod", 0.025, 0.45, (0.64, 0.10, 1.85), STEEL, verts=10)

# Elbow, forearm, gripper cradle with a seat in it.
box("Elbow", (0.16, 0.16, 0.18), (0.5, 0, 1.48), CHARCOAL)
box("Forearm", (0.72, 0.10, 0.10), (0.82, 0, 1.36), GREEN,
    rot=(0.0, 0.28, 0.0))
box("Wrist", (0.12, 0.12, 0.12), (1.14, 0, 1.22), CHARCOAL)
box("GripFrame", (0.52, 0.48, 0.06), (1.14, 0, 1.10), CHARCOAL)
for gy in (-0.20, 0.20):
    box("GripHook", (0.06, 0.05, 0.22), (1.36, gy, 1.02), STEEL,
        chamfer=False)
seat("Held", 1.14, 0, 0.72)

# Staged seats on a two-tier rack beside the far column.
box("RackFrame", (0.60, 1.10, 0.08), (-1.8, 0.85, 0.45), CHARCOAL)
box("RackFrameTop", (0.60, 1.10, 0.08), (-1.8, 0.85, 1.34), CHARCOAL)
for rz, ry in ((0.50, 0.55), (0.50, 1.15), (1.39, 0.85)):
    seat("Staged", -1.8, ry, rz)
for py in (0.35, 1.35):
    box("RackLeg", (0.08, 0.08, 1.18), (-1.8, py, 0.59), GREEN)

# Festoon loops along the rail, cabinet, and floor marking.
import bpy
from lb_model_kit import material
for n in range(4):
    bpy.ops.mesh.primitive_torus_add(
        location=(-1.2 + n * 0.55, 0, 2.78), rotation=(1.5708, 0.0, 0.0),
        major_radius=0.16, minor_radius=0.015,
        major_segments=20, minor_segments=8)
    loop = bpy.context.active_object
    loop.name = "FestoonLoop"
    loop.data.materials.append(material(*CHARCOAL))
box("Cabinet", (0.40, 0.30, 0.90), (1.95, -0.45, 0.45), GREEN)
box("CabDoor", (0.02, 0.26, 0.78), (1.74, -0.45, 0.45), CHARCOAL,
    chamfer=False)
box("FloorMark", (1.6, 0.05, 0.006), (0.9, 0.75, 0.003), YELLOW,
    chamfer=False)
box("FloorMark2", (1.6, 0.05, 0.006), (0.9, -0.75, 0.003), YELLOW,
    chamfer=False)
box("BalanceLink", (0.10, 0.12, 0.10), (0.64, 0.10, 2.82), CHARCOAL)

# Pendant and beacon on the near column.
box("Pendant", (0.18, 0.10, 0.26), (1.94, 0.18, 1.30), GREEN)
cyl("PendantEStop", 0.035, 0.04, (1.94, 0.25, 1.38), RED, axis="Y")
cyl("Beacon", 0.04, 0.09, (1.8, 0, 3.24), RED)

export("SM_LB_Assembly_SeatInstallManipulator_v001",
       "AssemblyShop/SeatManipulator_v001")
preview("SM_LB_Assembly_SeatInstallManipulator_v001",
        "AssemblyShop/SeatManipulator_v001")
