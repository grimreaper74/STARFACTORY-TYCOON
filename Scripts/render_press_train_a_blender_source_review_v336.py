"""Render the currently opened Train A Blender source from a fixed broadside studio view."""
from __future__ import annotations

import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def user_args() -> list[str]:
    return sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []


args = user_args()
if len(args) != 1:
    raise RuntimeError("Expected one output PNG path after --")
output = Path(args[0]).resolve()
if output.exists():
    raise RuntimeError(f"Refusing to overwrite {output}")
output.parent.mkdir(parents=True, exist_ok=True)

scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = False
scene.render.filepath = str(output)
scene.render.image_settings.color_mode = "RGBA"
scene.view_settings.look = "AgX - Medium High Contrast"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "MATERIAL"
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.display.shading.cavity_type = "WORLD"
scene.display.shading.show_specular_highlight = True
scene.display.shading.background_type = "VIEWPORT"
scene.display.shading.background_color = (0.08, 0.095, 0.11)

world = scene.world or bpy.data.worlds.new("LB_ReviewWorld")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.055, 0.065, 0.075, 1.0)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.32

renderables = [
    obj for obj in scene.objects
    if obj.type in {"MESH", "FONT", "CURVE", "SURFACE", "META"} and not obj.hide_render
]
if not renderables:
    raise RuntimeError("No renderable Train A objects found")

corners = []
for obj in renderables:
    corners.extend(obj.matrix_world @ Vector(corner) for corner in obj.bound_box)
mins = Vector((min(p.x for p in corners), min(p.y for p in corners), min(p.z for p in corners)))
maxs = Vector((max(p.x for p in corners), max(p.y for p in corners), max(p.z for p in corners)))
centre = (mins + maxs) * 0.5
size = maxs - mins

floor_z = mins.z - 0.03
bpy.ops.mesh.primitive_plane_add(size=max(size.x, size.y) * 1.35, location=(centre.x, centre.y, floor_z))
floor = bpy.context.object
floor.name = "LB_RENDER_ONLY_FLOOR"
mat = bpy.data.materials.new("LB_RenderFloor")
mat.diffuse_color = (0.075, 0.085, 0.09, 1.0)
mat.roughness = 0.82
floor.data.materials.append(mat)

camera_data = bpy.data.cameras.new("LB_RenderCamera")
camera = bpy.data.objects.new("LB_RenderCamera", camera_data)
scene.collection.objects.link(camera)
scene.camera = camera
camera.data.type = "ORTHO"
camera.data.lens = 52

# Choose the broadside automatically: the rebuilt source is long on Y, while
# the retained Unreal actor export is long on X.
if size.y >= size.x:
    camera.location = centre + Vector((max(size.x, size.z) * 2.2, -size.y * 0.08, size.z * 1.25))
    long_span = size.y
else:
    camera.location = centre + Vector((-size.x * 0.08, -max(size.y, size.z) * 2.2, size.z * 1.25))
    long_span = size.x
target = centre + Vector((0.0, 0.0, -size.z * 0.04))
camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
camera.data.ortho_scale = max(long_span * 1.10, size.z * 2.25)

def area(name: str, location: Vector, energy: float, colour: tuple[float, float, float], scale: float) -> None:
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.color = colour
    data.shape = "DISK"
    data.size = scale
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = (centre - obj.location).to_track_quat("-Z", "Y").to_euler()


span = max(size.x, size.y, size.z)
area("LB_Key", centre + Vector((span * 0.55, -span * 0.30, span * 0.55)), 2200, (1.0, 0.92, 0.78), span * 0.35)
area("LB_Fill", centre + Vector((-span * 0.42, -span * 0.18, span * 0.30)), 1500, (0.72, 0.84, 1.0), span * 0.32)
area("LB_Rim", centre + Vector((0.0, span * 0.32, span * 0.48)), 1900, (0.78, 1.0, 0.82), span * 0.28)

scene.render.image_settings.color_mode = "RGB"
bpy.ops.render.render(write_still=True)
print(f"LB_BLENDER_SOURCE_RENDER_PASS {output}")
