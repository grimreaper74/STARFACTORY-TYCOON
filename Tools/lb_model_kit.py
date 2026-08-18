"""Shared helpers for authoring fully detailed Line Boss machines.

No blockout tier (owner, 2026-08-18). The helpers exist so every machine gets the
things that separate a machine from a box: chamfered edges, flanged and gusseted
columns with cable trays, and real angled scissor linkages.

Blender-native, metres, floor pivot at the origin, brand-named slots, exported with
FBX_SCALE_UNITS plus bake_space_transform. Blender 5.2 engine enum is BLENDER_EEVEE.
"""
import math
import os

import bpy

OUT_ROOT = (r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8"
            r"/SourceAssets/Candidate")
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
        bsdf.inputs["Roughness"].default_value = 0.55
    MATERIALS[name] = mat
    return mat


def reset():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in list(bpy.data.meshes):
        bpy.data.meshes.remove(block)
    MATERIALS.clear()


def bevel(obj, width=0.012):
    mod = obj.modifiers.new("Bevel", "BEVEL")
    mod.width = width
    mod.segments = 2
    mod.limit_method = "ANGLE"
    mod.angle_limit = math.radians(40.0)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier="Bevel")


def box(name, size, loc, mat, rot=None, chamfer=True):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = (size[0], size[1], size[2])
    if rot:
        obj.rotation_euler = rot
    bpy.ops.object.transform_apply(scale=True, rotation=bool(rot))
    obj.data.materials.append(material(*mat))
    if chamfer:
        bevel(obj)
    return obj


def cyl(name, radius, depth, loc, mat, axis="Z", verts=20):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=loc,
                                        vertices=verts)
    obj = bpy.context.active_object
    obj.name = name
    if axis == "Y":
        obj.rotation_euler[0] = math.pi / 2
    elif axis == "X":
        obj.rotation_euler[1] = math.pi / 2
    if axis != "Z":
        bpy.ops.object.transform_apply(rotation=True)
    obj.data.materials.append(material(*mat))
    return obj


def scissor(prefix, centre, span, height, mat):
    length = math.hypot(span, height)
    angle = math.atan2(height, span)
    for sign in (1.0, -1.0):
        box(prefix + "Arm", (length, 0.09, 0.16), centre, mat,
            rot=(0.0, sign * angle, 0.0))
    cyl(prefix + "Pin", 0.05, 0.34, centre, STEEL, axis="Y")


def column(prefix, base, height, mat, width=0.24):
    box(prefix + "Plate", (width * 2.1, width * 2.1, 0.05),
        (base[0], base[1], base[2] + 0.025), CHARCOAL)
    box(prefix + "Shaft", (width, width, height),
        (base[0], base[1], base[2] + height / 2 + 0.05), mat)
    box(prefix + "Cap", (width * 1.5, width * 1.5, 0.06),
        (base[0], base[1], base[2] + height + 0.08), CHARCOAL)
    for sign in (1.0, -1.0):
        box(prefix + "Gusset", (0.05, width * 1.6, width * 1.6),
            (base[0] + sign * width * 0.55, base[1], base[2] + width * 0.9),
            CHARCOAL, rot=(0.0, sign * math.radians(38.0), 0.0))
    box(prefix + "Tray", (0.09, 0.05, height * 0.8),
        (base[0] - width * 0.62, base[1], base[2] + height * 0.45), STEEL)


def export(asset, folder):
    directory = os.path.join(OUT_ROOT, folder)
    os.makedirs(directory, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.export_scene.fbx(
        filepath=os.path.join(directory, asset + ".fbx"), use_selection=True,
        apply_scale_options="FBX_SCALE_UNITS", object_types={"MESH"},
        add_leaf_bones=False, bake_space_transform=True)
    print("EXPORTED", asset)


def preview(asset, folder, distance=11.0, height=6.0):
    bpy.ops.mesh.primitive_plane_add(size=40.0, location=(0, 0, 0))
    floor = bpy.context.active_object
    floor.data.materials.append(material("MAT_PreviewFloor", (0.19, 0.19, 0.18, 1.0)))
    cam_data = bpy.data.cameras.new("Cam")
    cam_data.lens = 45.0
    cam = bpy.data.objects.new("Cam", cam_data)
    bpy.context.collection.objects.link(cam)
    cam.location = (distance, -distance * 0.85, height)
    cam.rotation_euler = (math.radians(64.0), 0.0, math.radians(49.0))
    bpy.context.scene.camera = cam
    for name, energy, loc, rot in (
            ("Key", 5000.0, (7.0, -7.0, 10.0), (0.85, 0.0, 0.8)),
            ("Fill", 1500.0, (-8.0, 6.0, 7.0), (1.0, 0.0, -2.2))):
        light = bpy.data.objects.new(name, bpy.data.lights.new(name, type="AREA"))
        light.data.energy = energy
        light.data.size = 14.0
        light.location = loc
        light.rotation_euler = rot
        bpy.context.collection.objects.link(light)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1400
    scene.render.resolution_y = 900
    scene.world = bpy.data.worlds.new("W_" + asset)
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.05, 0.06, 0.08, 1.0)
    scene.render.filepath = os.path.join(OUT_ROOT, folder, asset + "_preview.png")
    bpy.ops.render.render(write_still=True)
    print("PREVIEW", asset)
