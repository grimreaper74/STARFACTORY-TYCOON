"""Render PR005 engineering reference views without saving or changing the source blend."""
import os
import math
import bpy
from mathutils import Vector

PROJECT = r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8"
OUT = os.path.join(PROJECT, "Saved", "ValidationScreenshots", "PR005", "MeshySkinDesignPack_v001")

def bbox(obj):
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    low = tuple(min(point[i] for point in points) for i in range(3))
    high = tuple(max(point[i] for point in points) for i in range(3))
    return low, high

def fmt(box):
    low, high = box
    return "min_mm=%s|max_mm=%s" % (tuple(round(v * 1000) for v in low), tuple(round(v * 1000) for v in high))

def render_material(name, color):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    material.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*color, 1)
    material.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.52
    return material

def setup(scene):
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 2000
    scene.render.resolution_y = 1400
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.world.color = (0.055, 0.055, 0.055)
    # Do not save; hide inherited utility floor/clearance helpers only for these review renders.
    for obj in scene.objects:
        if obj.name.startswith("CLR_") or obj.name == "RenderFloor":
            obj.hide_render = True
        if obj.type == "LIGHT":
            obj.hide_render = True
    stage = bpy.data.collections.new("TEMP_PR005_SKIN_REFERENCE_STAGE")
    scene.collection.children.link(stage)
    floor_mat = render_material("TEMP_StudioFloor", (0.58, 0.58, 0.56))
    bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, -0.01))
    floor = bpy.context.object
    floor.name = "TEMP_StudioFloor"
    floor.data.materials.append(floor_mat)
    for c in list(floor.users_collection): c.objects.unlink(floor)
    stage.objects.link(floor)
    def add_light(name, loc, power, size, colour, target):
        data = bpy.data.lights.new(name, "AREA")
        data.energy, data.shape, data.size, data.color = power, "DISK", size, colour
        obj = bpy.data.objects.new(name, data)
        stage.objects.link(obj)
        obj.location = loc
        obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()
    add_light("TEMP_Key", (-8, 10, 12), 1800, 6, (1, 1, 1), (0, 0, 1.5))
    add_light("TEMP_Fill", (8, 1, 8), 1300, 6, (0.88, 0.92, 1), (0, 0, 1.5))
    add_light("TEMP_Back", (0, -9, 8), 1300, 5, (1, 0.90, 0.78), (0, 0, 1.5))
    data = bpy.data.cameras.new("TEMP_PR005_REFERENCE_CAMERA")
    data.type = "ORTHO"
    data.ortho_scale = 13.0
    camera = bpy.data.objects.new("TEMP_PR005_REFERENCE_CAMERA", data)
    stage.objects.link(camera)
    scene.camera = camera
    return camera

def point(camera, loc, target, scale):
    camera.location = loc
    camera.data.ortho_scale = scale
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()

def main():
    scene = bpy.context.scene
    os.makedirs(OUT, exist_ok=True)
    print("PR005_ALL_ENGINEERING_OBJECT_BOUNDS")
    for obj in scene.objects:
        if obj.type == "MESH" and ("Mover" in obj.name or obj.name.startswith("CTX_SM_")):
            print("BOUND|%s|%s" % (obj.name, fmt(bbox(obj))))
    for obj in scene.objects:
        if obj.name.startswith("CLR_"):
            print("CLEARANCE|%s|loc_mm=%s|dim_mm=%s" % (obj.name, tuple(round(v * 1000) for v in obj.location), tuple(round(v * 1000) for v in obj.dimensions)))
    camera = setup(scene)
    views = {
        "01_PR005_Engineering_Front_Ortho.png": ((0, 15, 3.3), (0, 0.0, 1.65), 12.5),
        "02_PR005_Engineering_Rear_Ortho.png": ((0, -15, 3.3), (0, 0.0, 1.65), 12.5),
        "03_PR005_Engineering_Left_Ortho.png": ((-15, 0, 3.2), (0, 0, 1.65), 12.5),
        "04_PR005_Engineering_Right_Ortho.png": ((15, 0, 3.2), (0, 0, 1.65), 12.5),
        "05_PR005_Engineering_Top_Ortho.png": ((0, 0, 18), (0, 0, 0), 12.5),
        "06_PR005_Engineering_FrontThreeQuarter_Ortho.png": ((-12, 12, 9), (0, 0, 1.6), 13.0),
        "07_PR005_Engineering_RearThreeQuarter_Ortho.png": ((12, -12, 9), (0, 0, 1.6), 13.0),
    }
    for filename, (loc, target, scale) in views.items():
        point(camera, loc, target, scale)
        scene.render.filepath = os.path.join(OUT, filename)
        bpy.ops.render.render(write_still=True)
        print("RENDERED|" + scene.render.filepath)
    # Diagnostic: material override categorizes retained engineering modules without changing them.
    static = render_material("TEMP_DiagnosticStatic", (0.15, 0.23, 0.28))
    moving = render_material("TEMP_DiagnosticMoving", (0.78, 0.34, 0.05))
    process = render_material("TEMP_DiagnosticProcess", (0.75, 0.75, 0.72))
    for obj in scene.objects:
        if obj.type != "MESH": continue
        if "Mover" in obj.name:
            obj.active_material = moving
        elif "Strip" in obj.name or "Roll" in obj.name or "Mandrel" in obj.name:
            obj.active_material = process
        else:
            obj.active_material = static
    point(camera, (-12, 12, 9), (0, 0, 1.6), 13.0)
    scene.render.filepath = os.path.join(OUT, "08_PR005_Engineering_ComponentDiagnostic.png")
    bpy.ops.render.render(write_still=True)
    print("RENDERED|" + scene.render.filepath)
    print("SOURCE_NOT_SAVED")

if __name__ == "__main__":
    main()
