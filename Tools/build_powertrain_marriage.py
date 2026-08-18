"""Author the EV powertrain marriage station for general assembly.

The visual centrepiece of an assembly line and currently absent from the project
entirely. The owner confirmed on 2026-08-18 that the Cairnwell 2040 is FULLY ELECTRIC,
so this decks a high-voltage battery pack and a drive unit - not an engine and gearbox.

Conventions follow Tools/build_ed_line_modules.py: Blender-native (never Meshy), metres,
floor pivot at the origin, brand-named material slots, exported with
FBX_SCALE_UNITS + bake_space_transform so Blender metres land as Unreal centimetres.

Palette use is deliberate: Safety Yellow is functional only (floor outline, HV warning
band), Signal Red is reserved for alarms and appears once on the e-stop.
"""
import os

import bpy

OUT_ROOT = (r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8"
            r"/SourceAssets/Candidate/AssemblyShop")

MATERIALS = {}
GREEN = ("MAT_CairnwellGreen", (0.047, 0.153, 0.137, 1.0))
CHARCOAL = ("MAT_FoundryCharcoal", (0.055, 0.063, 0.071, 1.0))
STEEL = ("MAT_MachinedSteel", (0.44, 0.46, 0.48, 1.0))
WARMWHITE = ("MAT_WarmWhite", (0.88, 0.86, 0.80, 1.0))
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
    MATERIALS[name] = mat
    return mat


def reset():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in list(bpy.data.meshes):
        bpy.data.meshes.remove(block)
    MATERIALS.clear()


def box(name, size, location, mat):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = (size[0], size[1], size[2])
    bpy.ops.object.transform_apply(scale=True)
    obj.data.materials.append(material(*mat))
    return obj


def cyl(name, radius, depth, location, mat, axis="Z"):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth,
                                        location=location, vertices=16)
    obj = bpy.context.active_object
    obj.name = name
    if axis == "Y":
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
# Powertrain marriage station. 6.4 x 4.4 m, floor pivot at the origin, body
# carried overhead on the cross beam while two lift tables raise the pack and
# the drive unit into it from below - the standard decking arrangement.
# ---------------------------------------------------------------------------
reset()
W, D = 6.4, 4.4

# Foundation frame and the painted safety outline that bounds the cell.
box("BaseFrame", (W, D, 0.25), (0, 0, 0.125), CHARCOAL)
for sx in (-1, 1):
    box("OutlineX", (0.14, D, 0.03), (sx * (W / 2 - 0.07), 0, 0.265), YELLOW)
for sy in (-1, 1):
    box("OutlineY", (W, 0.14, 0.03), (0, sy * (D / 2 - 0.07), 0.265), YELLOW)

# Battery pack lift table: the large one, scissor legs beneath a steel deck.
box("PackDeck", (2.7, 1.7, 0.16), (-0.6, 0, 0.85), STEEL)
for sx in (-1, 1):
    for sy in (-1, 1):
        box("PackScissor", (0.12, 0.12, 0.55),
            (-0.6 + sx * 1.15, sy * 0.7, 0.52), CHARCOAL)
box("PackPad", (2.4, 1.4, 0.06), (-0.6, 0, 0.96), WARMWHITE)

# Drive unit lift table: smaller, at the front axle position.
box("DriveDeck", (1.3, 1.1, 0.14), (2.05, 0, 0.78), STEEL)
for sx in (-1, 1):
    box("DriveScissor", (0.11, 0.11, 0.5), (2.05 + sx * 0.5, 0, 0.48), CHARCOAL)

# Four alignment towers guide the body down onto the pack.
for sx in (-1, 1):
    for sy in (-1, 1):
        box("AlignTower", (0.2, 0.2, 2.5),
            (sx * (W / 2 - 0.45), sy * (D / 2 - 0.4), 1.25), GREEN)
        cyl("AlignCone", 0.09, 0.3,
            (sx * (W / 2 - 0.45), sy * (D / 2 - 0.4), 2.6), STEEL)

# Overhead cross beam carrying the body, with two torque balancers.
box("CrossBeam", (0.34, D + 0.4, 0.4), (0.2, 0, 2.72), GREEN)
for sy in (-1, 1):
    cyl("Balancer", 0.11, 0.5, (0.2, sy * 1.1, 2.28), CHARCOAL)
    cyl("BalancerCord", 0.02, 0.9, (0.2, sy * 1.1, 1.62), STEEL)

# HV interlock cabinet - characteristic of an EV line - with its warning band.
box("HVCabinet", (0.85, 0.45, 1.65), (-W / 2 + 0.5, -D / 2 + 0.35, 0.95), GREEN)
box("HVWarnBand", (0.87, 0.47, 0.14), (-W / 2 + 0.5, -D / 2 + 0.35, 1.62), YELLOW)

# Operator HMI pedestal, and one e-stop in Signal Red.
box("HMIPost", (0.22, 0.22, 1.05), (W / 2 - 0.55, -D / 2 + 0.4, 0.65), CHARCOAL)
box("HMIHead", (0.62, 0.16, 0.44), (W / 2 - 0.55, -D / 2 + 0.4, 1.32), GREEN)
box("HMIScreen", (0.5, 0.03, 0.32), (W / 2 - 0.55, -D / 2 + 0.31, 1.32), WARMWHITE)
cyl("EStop", 0.07, 0.08, (W / 2 - 0.55, -D / 2 + 0.32, 1.02), RED)

export("SM_LB_Assembly_PowertrainMarriage_v001", "PowertrainMarriage_v001")
