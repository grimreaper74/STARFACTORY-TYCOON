import bpy
import math
import os
import sys
from mathutils import Vector

source = sys.argv[sys.argv.index("--") + 1]
output = sys.argv[sys.argv.index("--") + 2]
bpy.ops.wm.open_mainfile(filepath=source)
os.makedirs(output, exist_ok=True)

meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
points = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
minimum = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
maximum = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
centre = (minimum + maximum) * 0.5
size = maximum - minimum

material = bpy.data.materials.new("NeutralClay")
material.diffuse_color = (0.12, 0.20, 0.15, 1.0)
material.metallic = 0.25
material.roughness = 0.48
for obj in meshes:
    obj.data.materials.clear()
    obj.data.materials.append(material)

bpy.ops.mesh.primitive_plane_add(size=max(size.x, size.y) * 5.0,
    location=(centre.x, centre.y, minimum.z - 0.005))
floor = bpy.context.object
floor_mat = bpy.data.materials.new("NeutralFloor")
floor_mat.diffuse_color = (0.12, 0.12, 0.12, 1.0)
floor_mat.roughness = 0.8
floor.data.materials.append(floor_mat)

bpy.ops.object.light_add(type="AREA", location=(centre.x - 3.0, centre.y - 4.0, maximum.z + 4.0))
bpy.context.object.data.energy = 850.0
bpy.context.object.data.shape = "DISK"
bpy.context.object.data.size = 5.0
bpy.ops.object.light_add(type="AREA", location=(centre.x + 4.0, centre.y + 2.0, centre.z + 2.0))
bpy.context.object.data.energy = 450.0
bpy.context.object.data.size = 4.0

bpy.ops.object.camera_add()
camera = bpy.context.object
bpy.context.scene.camera = camera
camera.data.lens = 58

def point_camera(target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()

distance = max(size) * 2.6
views = {
    "01_hero": centre + Vector((distance * 0.75, -distance, distance * 0.62)),
    "02_front": centre + Vector((0.0, -distance, size.z * 0.08)),
    "03_left": centre + Vector((-distance, 0.0, size.z * 0.08)),
    "04_rear": centre + Vector((0.0, distance, size.z * 0.08)),
}
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1280
scene.render.resolution_y = 960
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.world.color = (0.025, 0.025, 0.025)
for name, location in views.items():
    camera.location = location
    point_camera(centre)
    scene.render.filepath = os.path.join(output, name + ".png")
    bpy.ops.render.render(write_still=True)
