"""Render a Blender review model of the native Train A presentation.

This is deliberately a clean, solid-colour proxy for the Unreal-native press
train.  It is a review aid, not a Meshy import or manufacturing drawing.
"""
import bpy
import math
import os
from mathutils import Vector

OUT = r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Saved\Previews\NativePressTrain"
os.makedirs(OUT, exist_ok=True)

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

def material(name, colour, metallic=0.0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*colour, 1.0)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*colour, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.38
    bsdf.inputs["Metallic"].default_value = metallic
    return m

GREEN = material("Cairnwell factory green", (0.035, 0.17, 0.10), 0.65)
STEEL = material("Transfer steel", (0.14, 0.19, 0.22), 0.75)
YELLOW = material("Safety yellow", (0.95, 0.46, 0.015), 0.25)
FLOOR = material("Concrete", (0.26, 0.29, 0.30), 0.0)
WHITE = material("Die steel", (0.48, 0.52, 0.55), 0.7)

def box(name, loc, scale, mat, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    ob = bpy.context.object
    ob.name = name
    ob.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ob.data.materials.append(mat)
    if bevel:
        mod = ob.modifiers.new("Small edge rounds", "BEVEL")
        mod.width = bevel
        mod.segments = 2
    return ob

def cylinder(name, loc, radius, depth, mat, rot=(0,0,0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=radius, depth=depth, location=loc, rotation=rot)
    ob = bpy.context.object
    ob.name = name
    ob.data.materials.append(mat)
    return ob

# Floor and train datum. Blender units are metres.
box("Factory floor", (0, 0, -0.15), (18, 58, 0.15), FLOOR)
box("Operator walkway", (-8.9, 0, 0.015), (1.25, 56, 0.02), YELLOW)
box("Service walkway", (8.9, 0, 0.015), (1.25, 56, 0.02), YELLOW)

station_names = ["S01  DESTACK", "S02  DEEP DRAW", "S03  RESTRIKE", "S04  TRIM", "S05  PIERCE", "S06  HEM", "S07  INSPECT"]
pitch = 15.0
for i, label in enumerate(station_names):
    y = (i - 3) * pitch
    # Main press body: bed, crown, broad side frames and visible die space.
    box(label + " base", (0, y, 0.55), (7.8, 5.1, 0.55), GREEN, 0.08)
    box(label + " bed", (0, y, 3.5), (5.55, 3.65, 0.34), STEEL, 0.06)
    box(label + " crown", (0, y, 13.75), (7.35, 4.15, 1.85), GREEN, 0.12)
    for side in (-1, 1):
        box(label + " upright", (side * 5.95, y, 7.9), (1.35, 1.35, 7.15), GREEN, 0.08)
        box(label + " side housing", (side * 6.5, y, 9.2), (0.72, 3.75, 4.7), GREEN, 0.06)
        # Guard posts + longitudinal rails.
        for end in (-5.1, 5.1):
            box(label + " guard post", (side * 9.8, y + end, 7.5), (0.13, 0.13, 4.3), YELLOW)
        box(label + " guard rail", (side * 9.8, y, 9.1), (0.10, 4.85, 0.10), YELLOW)
    # Die and a clearly separate moving ram.
    box(label + " die", (0, y, 4.45), (4.6, 2.9, 0.42), WHITE, 0.08)
    box(label + " ram", (0, y, 10.6 - (i % 3) * 0.6), (4.8, 2.95, 0.55), STEEL, 0.06)
    # Operator HMI / stack light and service hydraulic cabinet.
    box(label + " HMI", (-11.1, y - 5.6, 2.05), (0.34, 0.24, 1.5), STEEL, 0.03)
    cylinder(label + " stack light", (-11.1, y - 5.6, 5.6), 0.1, 1.1, YELLOW)
    box(label + " hydraulic cabinet", (9.7, y + 2.5, 4.8), (0.88, 1.1, 1.25), STEEL, 0.06)
    # Different process silhouettes.
    if i == 0:
        box("Blank stack", (0, y - 4.2, 5.0), (3.8, 2.2, 1.7), WHITE)
    elif i == 3:
        for side in (-1, 1):
            box("Scrap chute", (side * 6.2, y + 4.0, 3.0), (0.55, 1.4, 0.45), STEEL)
    elif i == 4:
        for x in (-3.0, -1.0, 1.0, 3.0):
            cylinder("Pierce tool", (x, y, 7.8), 0.23, 4.2, STEEL)
    elif i == 6:
        for side in (-1, 1):
            box("Inspection gantry", (side * 8.2, y, 8.8), (0.3, 0.3, 5.2), STEEL)
        box("Inspection beam", (0, y, 13.2), (8.5, 0.35, 0.30), STEEL)

# Full length transfer system and service tray: critical to reading it as a train.
for side in (-1, 1):
    box("Full length transfer rail", (side * 4.7, 0, 19.0), (0.20, 52.0, 0.20), STEEL)
    box("Full length service rail", (side * 9.1, 0, 18.6), (0.16, 52.0, 0.16), STEEL)
for y in (-37.5, -7.5, 22.5):
    box("Transfer carriage", (0, y, 18.65), (5.4, 1.1, 0.35), STEEL, 0.06)
    box("Vacuum beam", (0, y, 16.7), (4.8, 0.30, 0.24), YELLOW)
    for x in (-3.5, -1.2, 1.2, 3.5):
        cylinder("Vacuum cup", (x, y, 15.8), 0.28, 0.7, STEEL)

# Simple studio lighting.
bpy.ops.object.light_add(type="AREA", location=(0, 0, 34))
bpy.context.object.data.energy = 25000
bpy.context.object.data.shape = "RECTANGLE"
bpy.context.object.data.size = 38
bpy.context.object.data.size_y = 115
bpy.ops.object.light_add(type="AREA", location=(-25, -18, 16))
bpy.context.object.data.energy = 8000
bpy.context.object.data.size = 20
bpy.context.object.rotation_euler = (math.radians(65), 0, math.radians(-55))

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1600
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.world.color = (0.025, 0.035, 0.045)

def camera_render(name, location, target, lens):
    bpy.ops.object.camera_add(location=location)
    cam = bpy.context.object
    direction = Vector(target) - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = lens
    scene.camera = cam
    scene.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam, do_unlink=True)

camera_render("native_press_train_overview", (36, -72, 42), (0, 0, 8), 38)
camera_render("native_press_train_close", (24, -34, 17), (0, -15, 8), 42)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "NativePressTrainReview.blend"))
