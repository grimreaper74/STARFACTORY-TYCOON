import bpy
import math
import sys
from pathlib import Path
from mathutils import Vector


source = Path(sys.argv[sys.argv.index("--") + 1])
output = Path(sys.argv[sys.argv.index("--") + 2])

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(source))
meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
if not meshes:
    raise RuntimeError("No mesh objects imported")

material = bpy.data.materials.new("LB_Audit_Green")
material.diffuse_color = (0.035, 0.16, 0.10, 1.0)
material.metallic = 0.5
material.roughness = 0.32
for obj in meshes:
    obj.data.materials.clear()
    obj.data.materials.append(material)

corners = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
mins = Vector(tuple(min(c[i] for c in corners) for i in range(3)))
maxs = Vector(tuple(max(c[i] for c in corners) for i in range(3)))
center = (mins + maxs) * 0.5
size = max(maxs - mins)

bpy.ops.mesh.primitive_plane_add(size=size * 4, location=(center.x, center.y, mins.z - size * 0.01))
floor = bpy.context.object
floor_mat = bpy.data.materials.new("LB_Audit_Floor")
floor_mat.diffuse_color = (0.12, 0.13, 0.14, 1.0)
floor_mat.roughness = 0.7
floor.data.materials.append(floor_mat)

camera_data = bpy.data.cameras.new("AuditCamera")
camera = bpy.data.objects.new("AuditCamera", camera_data)
bpy.context.scene.collection.objects.link(camera)
camera.location = center + Vector((size * 1.35, -size * 1.7, size * 1.05))
direction = center - camera.location
camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
camera_data.lens = 58
bpy.context.scene.camera = camera

scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.studio_light = "paint.sl"
scene.display.shading.color_type = "MATERIAL"
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.display.shading.cavity_type = "WORLD"
scene.display.shading.curvature_ridge_factor = 1.5
scene.display.shading.curvature_valley_factor = 1.2
scene.display.shading.background_type = "WORLD"
scene.render.resolution_x = 1280
scene.render.resolution_y = 960
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = str(output)
scene.render.film_transparent = False
scene.world = bpy.data.worlds.new("LB_Audit_World")
scene.world.color = (0.015, 0.018, 0.02)
bpy.ops.render.render(write_still=True)
print(f"LB_RENDER={output}")
