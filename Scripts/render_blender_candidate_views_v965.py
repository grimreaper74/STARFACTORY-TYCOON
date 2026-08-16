"""Render matching orthographic review views for any Blender candidate."""
import bpy
import sys
from pathlib import Path
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if len(args) != 2:
    raise RuntimeError("usage: -- <label> <output-directory>")
label, output_arg = args
output = Path(output_arg)
output.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1600
scene.render.resolution_y = 1600
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
if scene.world is None:
    scene.world = bpy.data.worlds.new("CandidateReviewWorld")
scene.world.color = (0.025, 0.025, 0.025)
meshes = [obj for obj in scene.objects if obj.type == "MESH" and not obj.hide_render]
points = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
low = Vector(tuple(min(point[i] for point in points) for i in range(3)))
high = Vector(tuple(max(point[i] for point in points) for i in range(3)))
center = (low + high) * 0.5
size = high - low
span = max(size)

def aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()

bpy.ops.mesh.primitive_plane_add(size=max(15, span * 3), location=(center.x, center.y, low.z - 0.01))
floor = bpy.context.object
floor_material = bpy.data.materials.new("CandidateReviewFloor")
floor_material.diffuse_color = (0.12, 0.13, 0.14, 1)
floor_material.roughness = 0.82
floor.data.materials.append(floor_material)
for name, direction, energy in [
    ("Key", Vector((-1, -1, 1.2)), 1900),
    ("Fill", Vector((1, -0.4, 0.8)), 1100),
    ("Rim", Vector((0.2, 1, 1.1)), 1500),
]:
    light_data = bpy.data.lights.new(name, "AREA")
    light_data.energy = energy
    light_data.size = max(2, span * 0.8)
    light = bpy.data.objects.new(name, light_data)
    scene.collection.objects.link(light)
    light.location = center + direction.normalized() * span * 2
    aim(light, center)
camera_data = bpy.data.cameras.new("CandidateReviewCamera")
camera = bpy.data.objects.new("CandidateReviewCamera", camera_data)
scene.collection.objects.link(camera)
camera_data.type = "ORTHO"
camera_data.ortho_scale = span * 1.32
scene.camera = camera
for view, direction in {
    "front": Vector((0, -1, 0.12)),
    "left": Vector((-1, 0, 0.12)),
    "right": Vector((1, 0, 0.12)),
    "rear": Vector((0, 1, 0.12)),
    "elevated": Vector((1, -1, 0.75)),
}.items():
    camera.location = center + direction.normalized() * span * 3
    aim(camera, center)
    scene.render.filepath = str(output / f"{label}_{view}.png")
    bpy.ops.render.render(write_still=True)
print("LINE_BOSS_CANDIDATE_RENDER_V965", label, list(size), len(meshes), output)
