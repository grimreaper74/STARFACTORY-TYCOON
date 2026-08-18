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
    """A crossed scissor pair with pivot bosses, a guide rail and a cross tie.

    A lift table is recognised by its linkage, so this is deliberately more than two
    angled bars: each arm gets an end boss, the pair shares a centre pin with visible
    bosses either side, and a guide rail plus tie bar read as the parts that stop the
    deck racking.
    """
    length = math.hypot(span, height)
    angle = math.atan2(height, span)
    for sign in (1.0, -1.0):
        box(prefix + "Arm", (length, 0.075, 0.17), centre, mat,
            rot=(0.0, sign * angle, 0.0))
        # End bosses where the arm pins into the frame and the deck.
        for end in (-1.0, 1.0):
            ex = centre[0] + end * math.cos(angle) * length * 0.5
            ez = centre[2] + end * sign * math.sin(angle) * length * 0.5
            cyl(prefix + "Boss", 0.055, 0.13, (ex, centre[1], ez), STEEL, axis="Y")
    # Centre pin with a boss each side.
    cyl(prefix + "Pin", 0.032, 0.4, centre, STEEL, axis="Y")
    for side in (-1.0, 1.0):
        cyl(prefix + "PinBoss", 0.06, 0.07,
            (centre[0], centre[1] + side * 0.16, centre[2]), CHARCOAL, axis="Y")
    # Guide rail the lower arm end runs in, and a tie bar across the pair.
    box(prefix + "Rail", (span * 1.05, 0.07, 0.06),
        (centre[0], centre[1], centre[2] - height * 0.5), STEEL)
    box(prefix + "Tie", (0.05, 0.3, 0.05),
        (centre[0], centre[1], centre[2] + height * 0.32), CHARCOAL)


def column(prefix, base, height, mat, width=0.24):
    """A fabricated column: bolted base plate, tapered shaft, gussets, tray, junction box.

    Plain extrusions read as posts. What makes a column look fabricated is the
    hardware at its ends and the services strapped to it, so the base plate gets
    corner bolts, the shaft steps in above mid height, and a junction box sits on the
    cable tray.
    """
    plate = width * 2.1
    box(prefix + "Plate", (plate, plate, 0.05),
        (base[0], base[1], base[2] + 0.025), CHARCOAL)
    # Holding-down bolts at the plate corners.
    for bx in (-1.0, 1.0):
        for by in (-1.0, 1.0):
            cyl(prefix + "Bolt", 0.022, 0.06,
                (base[0] + bx * plate * 0.36, base[1] + by * plate * 0.36,
                 base[2] + 0.07), STEEL, verts=10)
    # Shaft in two stages so it tapers rather than reading as one bar.
    lower = height * 0.58
    box(prefix + "Shaft", (width, width, lower),
        (base[0], base[1], base[2] + lower / 2 + 0.05), mat)
    box(prefix + "ShaftUpper", (width * 0.78, width * 0.78, height - lower),
        (base[0], base[1], base[2] + lower + (height - lower) / 2 + 0.05), mat)
    box(prefix + "Splice", (width * 1.12, width * 1.12, 0.05),
        (base[0], base[1], base[2] + lower + 0.05), CHARCOAL)
    box(prefix + "Cap", (width * 1.4, width * 1.4, 0.06),
        (base[0], base[1], base[2] + height + 0.08), CHARCOAL)
    for sign in (1.0, -1.0):
        box(prefix + "Gusset", (0.05, width * 1.7, width * 1.7),
            (base[0] + sign * width * 0.55, base[1], base[2] + width * 0.95),
            CHARCOAL, rot=(0.0, sign * math.radians(38.0), 0.0))
    # Cable tray up the column with a junction box and a conduit drop.
    box(prefix + "Tray", (0.1, 0.06, height * 0.8),
        (base[0] - width * 0.66, base[1], base[2] + height * 0.45), STEEL)
    box(prefix + "JBox", (0.16, 0.13, 0.2),
        (base[0] - width * 0.78, base[1], base[2] + height * 0.62), GREEN)
    cyl(prefix + "Conduit", 0.028, height * 0.5,
        (base[0] - width * 0.66, base[1] + 0.09, base[2] + height * 0.3), STEEL)


def export(asset, folder):
    directory = os.path.join(OUT_ROOT, folder)
    os.makedirs(directory, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.export_scene.fbx(
        filepath=os.path.join(directory, asset + ".fbx"), use_selection=True,
        apply_scale_options="FBX_SCALE_UNITS", object_types={"MESH"},
        add_leaf_bones=False, bake_space_transform=True)
    print("EXPORTED", asset)


def preview(asset, folder, distance=None, height=None):
    """Render a three-quarter view framed on the model's own bounds.

    Earlier previews used hand-picked camera distances and cropped the top off tall
    machines while filling half the frame with floor, which made judging the detail
    level unreliable. Measure the geometry and place the camera from that instead.
    """
    import mathutils

    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    lo = mathutils.Vector((1e9, 1e9, 1e9))
    hi = mathutils.Vector((-1e9, -1e9, -1e9))
    for obj in meshes:
        for corner in obj.bound_box:
            world = obj.matrix_world @ mathutils.Vector(corner)
            lo = mathutils.Vector(map(min, lo, world))
            hi = mathutils.Vector(map(max, hi, world))
    centre = (lo + hi) * 0.5
    radius = max((hi - lo).length * 0.5, 0.5)

    bpy.ops.mesh.primitive_plane_add(size=radius * 14.0,
                                     location=(centre.x, centre.y, lo.z - 0.01))
    floor = bpy.context.active_object
    floor.data.materials.append(material("MAT_PreviewFloor", (0.19, 0.19, 0.18, 1.0)))

    cam_data = bpy.data.cameras.new("Cam")
    cam_data.lens = 50.0
    cam = bpy.data.objects.new("Cam", cam_data)
    bpy.context.collection.objects.link(cam)
    # Pull back proportionally to the model, on a fixed three-quarter bearing.
    reach = radius * 2.9
    cam.location = (centre.x + reach * 0.72, centre.y - reach * 0.72,
                    centre.z + reach * 0.52)
    direction = centre - mathutils.Vector(cam.location)
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = cam

    for name, energy, offset in (
            ("Key", 1.0, (1.0, -1.0, 1.5)),
            ("Fill", 0.28, (-1.2, 0.9, 1.0))):
        light = bpy.data.objects.new(name, bpy.data.lights.new(name, type="AREA"))
        light.data.energy = energy * 220.0 * radius * radius
        light.data.size = radius * 3.0
        light.location = (centre.x + offset[0] * reach, centre.y + offset[1] * reach,
                          centre.z + offset[2] * reach)
        aim = centre - mathutils.Vector(light.location)
        light.rotation_euler = aim.to_track_quat("-Z", "Y").to_euler()
        bpy.context.collection.objects.link(light)

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1400
    scene.render.resolution_y = 1000
    scene.world = bpy.data.worlds.new("W_" + asset)
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.06, 0.07, 0.09, 1.0)
        bg.inputs["Strength"].default_value = 0.6
    scene.render.filepath = os.path.join(OUT_ROOT, folder, asset + "_preview.png")
    bpy.ops.render.render(write_still=True)
    print("PREVIEW", asset)
