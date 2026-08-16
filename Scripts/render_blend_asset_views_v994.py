"""Render neutral, repeatable Blender views without modifying the source file."""
import bpy
import json
import os
import sys
from mathutils import Vector


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if len(args) != 1:
    raise RuntimeError("usage: blender <source.blend> --python script -- <output-directory>")
output = os.path.abspath(args[0])
os.makedirs(output, exist_ok=True)

meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH" and not obj.hide_render]
if not meshes:
    raise RuntimeError("source has no renderable meshes")

corners = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
low = Vector(tuple(min(point[i] for point in corners) for i in range(3)))
high = Vector(tuple(max(point[i] for point in corners) for i in range(3)))
dims = high - low
centre = (low + high) * 0.5

# Keep the source asset untouched; centre and floor-seat only this open render session.
offset = Vector((-centre.x, -centre.y, -low.z))
for obj in meshes:
    obj.location += offset
centre = Vector((0.0, 0.0, dims.z * 0.5))

floor_mat = bpy.data.materials.new("M_LB_NeutralFloor_v994")
floor_mat.diffuse_color = (0.12, 0.12, 0.12, 1.0)
floor_mat.metallic = 0.0
floor_mat.roughness = 0.86
bpy.ops.mesh.primitive_plane_add(size=max(dims.x, dims.y) * 4.0, location=(0.0, 0.0, -0.004))
bpy.context.object.data.materials.append(floor_mat)

scene = bpy.context.scene
if scene.world is None:
    scene.world = bpy.data.worlds.new("World_LB_Neutral_v994")
scene.world.color = (0.055, 0.055, 0.055)
for location, energy, size in (
    ((-3.0, -4.0, 5.5), 900.0, 4.0),
    ((4.0, 1.5, 3.5), 550.0, 3.5),
    ((0.0, 4.0, 4.5), 350.0, 3.0),
):
    bpy.ops.object.light_add(type="AREA", location=location)
    light = bpy.context.object
    light.data.energy = energy
    light.data.shape = "DISK"
    light.data.size = size
    look_at(light, centre)

bpy.ops.object.camera_add()
camera = bpy.context.object
scene.camera = camera
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1024
scene.render.resolution_y = 1024
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.view_settings.look = "AgX - Medium High Contrast"

distance = max(dims.x, dims.y, dims.z) * 3.0
views = {
    "front_negative_y": Vector((0.0, -distance, centre.z)),
    "rear_positive_y": Vector((0.0, distance, centre.z)),
    "left_negative_x": Vector((-distance, 0.0, centre.z)),
    "right_positive_x": Vector((distance, 0.0, centre.z)),
    "hero": Vector((-distance * 0.72, -distance * 0.72, max(dims.z * 1.45, centre.z + 0.5))),
}
renders = []
for name, location in views.items():
    camera.location = location
    look_at(camera, centre)
    if name == "hero":
        camera.data.type = "PERSP"
        camera.data.lens = 55.0
    else:
        camera.data.type = "ORTHO"
        if "negative_y" in name or "positive_y" in name:
            camera.data.ortho_scale = max(dims.x, dims.z) * 1.25
        else:
            camera.data.ortho_scale = max(dims.y, dims.z) * 1.25
    path = os.path.join(output, name + ".png")
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    renders.append(path)

payload = {
    "status": "PASS__NEUTRAL_BLENDER_VIEWS_RENDERED__SOURCE_NOT_MODIFIED",
    "source": bpy.data.filepath,
    "mesh_count": len(meshes),
    "dimensions_m": [round(value, 6) for value in dims],
    "renders": renders,
}
with open(os.path.join(output, "render_manifest_v994.json"), "w", encoding="utf-8") as handle:
    json.dump(payload, handle, indent=2)
print("LINE_BOSS_BLEND_ASSET_VIEWS_V994", len(renders))
