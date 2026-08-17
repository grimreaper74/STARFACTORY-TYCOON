"""Author the ED line's missing production modules, per the owner's reference.

The reference arrangement is a series of open dip tanks under an overhead
carrier gantry, followed by a long enclosed oven with roof blowers. The tanks
already exist as authored modules; the oven was still blockout geometry and
there was no carrier gantry at all. This builds both as repeatable segments so
they tile along the line, Blender-native, metres, floor pivots, brand slots.
"""
import os
import sys

import bpy

OUT_ROOT = (r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8"
            r"/SourceAssets/Candidate/PaintShop")

MATERIALS = {}
GREEN = ("MAT_CairnwellGreen", (0.047, 0.153, 0.137, 1.0))
CHARCOAL = ("MAT_FoundryCharcoal", (0.055, 0.063, 0.071, 1.0))
STEEL = ("MAT_MachinedSteel", (0.44, 0.46, 0.48, 1.0))
YELLOW = ("MAT_SafetyYellow", (0.83, 0.68, 0.0, 1.0))
RED = ("MAT_SignalRed", (0.62, 0.11, 0.09, 1.0))


def material(name, rgba):
    if name in MATERIALS:
        return MATERIALS[name]
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = rgba
        bsdf.inputs["Roughness"].default_value = 0.55
    MATERIALS[name] = mat
    return mat


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    MATERIALS.clear()


def box(name, size, location, mat, bevel=0.008):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = (size[0] * 0.5, size[1] * 0.5, size[2] * 0.5)
    bpy.ops.object.transform_apply(scale=True)
    if bevel > 0.0:
        mod = obj.modifiers.new("Bevel", "BEVEL")
        mod.width = bevel
        mod.segments = 2
    obj.data.materials.append(material(*mat))
    return obj


def cyl(name, radius, depth, location, mat, verts=32, axis="Z"):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=verts, radius=radius, depth=depth, location=location)
    obj = bpy.context.active_object
    obj.name = name
    if axis == "X":
        obj.rotation_euler[1] = 1.5707963
    elif axis == "Y":
        obj.rotation_euler[0] = 1.5707963
    bpy.ops.object.transform_apply(rotation=True)
    obj.data.materials.append(material(*mat))
    return obj


def export(asset_name, folder):
    directory = os.path.join(OUT_ROOT, folder)
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, asset_name + ".fbx")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.export_scene.fbx(
        filepath=path, use_selection=True,
        apply_scale_options="FBX_SCALE_UNITS",
        object_types={"MESH"}, add_leaf_bones=False,
        bake_space_transform=True)
    print("EXPORTED", path)


# ---------------------------------------------------------------------------
# 1. Oven segment: one repeatable 4 m bay of the long cure oven. Dark green
#    panelled shell, a roof blower with its plenum, a side access door with
#    inspection window, and the railed roof walkway the reference shows.
# ---------------------------------------------------------------------------
reset()
SEG = 4.0
box("Shell", (SEG, 4.4, 4.6), (0, 0, 2.3), GREEN)
box("ShellBase", (SEG, 4.6, 0.35), (0, 0, 0.175), CHARCOAL)
# Panel seams: shallow pilasters break the long flank into bays.
for sx in (-1.5, 1.5):
    box("Pilaster", (0.12, 4.46, 4.2), (sx, 0, 2.3), CHARCOAL, bevel=0.0)
# Side access door with a window and handle bar.
box("Door", (1.5, 0.10, 2.5), (0, -2.22, 1.45), CHARCOAL)
box("DoorWindow", (0.7, 0.06, 0.5), (0, -2.27, 2.3), STEEL, bevel=0.0)
box("DoorHandle", (0.9, 0.08, 0.10), (0, -2.30, 1.25), YELLOW)
# Roof blower: plenum box, drum housing and stack.
box("Plenum", (2.2, 2.4, 0.45), (0, 0, 4.82), CHARCOAL)
cyl("BlowerDrum", 0.85, 1.05, (0, 0, 5.55), STEEL, verts=40)
cyl("BlowerNeck", 0.30, 0.7, (0, 1.35, 5.2), STEEL, verts=24)
cyl("Stack", 0.26, 0.9, (0, -1.3, 5.45), STEEL, verts=24)
# Railed roof walkway along the service side.
box("Walkway", (SEG, 0.95, 0.08), (0, 2.55, 4.64), STEEL)
box("WalkwayRail", (SEG, 0.06, 0.95), (0, 2.98, 5.10), YELLOW)
for rx in (-1.7, 0.0, 1.7):
    box("RailPost", (0.08, 0.08, 0.95), (rx, 2.98, 5.10), YELLOW, bevel=0.0)
# Control cabinet on the flank, and a red isolation box.
box("Cabinet", (0.55, 0.28, 1.35), (-1.6, -2.32, 0.85), GREEN)
box("Isolator", (0.24, 0.16, 0.30), (1.75, -2.30, 1.30), RED)
export("SM_LB_EDLine_OvenSegment_v002", "EDLineOven_v002")

# ---------------------------------------------------------------------------
# 2. Carrier gantry bay: the overhead structure bodies hang from over the
#    tanks - two columns, the top beam, a hanger carriage with its crossbar,
#    and the stack light the reference puts above every station.
# ---------------------------------------------------------------------------
reset()
BAY = 3.24  # Matches the authored tank pitch of 324 cm.
for sy in (-2.35, 2.35):
    box("Column", (0.26, 0.26, 5.2), (0, sy, 2.6), CHARCOAL)
    box("ColumnFoot", (0.55, 0.55, 0.14), (0, sy, 0.07), STEEL)
    box("ColumnKick", (0.30, 0.30, 0.55), (0, sy, 0.35), YELLOW, bevel=0.0)
box("TopBeam", (BAY, 0.30, 0.40), (0, 0, 5.35), CHARCOAL)
box("CrossBeam", (0.28, 5.0, 0.34), (0, 0, 5.05), CHARCOAL)
# Running rails the carriages ride.
for ry in (-0.55, 0.55):
    box("Rail", (BAY, 0.12, 0.16), (0, ry, 4.80), STEEL)
# Hanger carriage: trolley, drop tubes and the body crossbar.
box("Trolley", (0.85, 1.5, 0.28), (0, 0, 4.62), STEEL)
for dx in (-0.34, 0.34):
    cyl("DropTube", 0.07, 1.5, (dx, 0, 3.80), STEEL, verts=16)
box("Crossbar", (1.3, 2.1, 0.16), (0, 0, 3.00), STEEL)
for hy in (-0.85, 0.85):
    box("Hook", (0.12, 0.12, 0.35), (0, hy, 2.78), STEEL, bevel=0.0)
# Stack light on the beam.
box("StackBracket", (0.16, 0.16, 0.30), (1.2, -0.35, 5.65), CHARCOAL)
cyl("StackRed", 0.11, 0.16, (1.2, -0.35, 5.88), RED, verts=16)
cyl("StackAmber", 0.11, 0.16, (1.2, -0.35, 6.04), YELLOW, verts=16)
cyl("StackGreen", 0.11, 0.16, (1.2, -0.35, 6.20), ("MAT_StatusGreen",
    (0.14, 0.62, 0.35, 1.0)), verts=16)
export("SM_LB_EDLine_CarrierGantryBay_v001", "EDLineGantry_v001")

print("ED_LINE_MODULES_BUILT")
sys.exit(0)
