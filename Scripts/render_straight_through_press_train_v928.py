"""Render proof views of the v928 straight-through player-placeable press train."""
import bpy
from pathlib import Path
from mathutils import Vector

OUT_DIR = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Saved\ValidationScreenshots\PressShop\Blender_v928")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def point_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 2400
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = False
scene.world.color = (0.018, 0.018, 0.018)

# Neutral review floor; the saved asset remains untouched because Blender is invoked without save.
bpy.ops.mesh.primitive_plane_add(size=120.0, location=(0.0, 0.0, -0.03))
floor = bpy.context.object
floor.name = "V928_ReviewFloor"
mat = bpy.data.materials.new("V928_ReviewFloorMaterial")
mat.diffuse_color = (0.10, 0.11, 0.12, 1.0)
mat.roughness = 0.82
floor.data.materials.append(mat)

for name, loc, energy, size in [
    ("V928_Key", (-18.0, -22.0, 24.0), 4200.0, 20.0),
    ("V928_Fill", (22.0, -14.0, 16.0), 3000.0, 18.0),
    ("V928_Rim", (0.0, 18.0, 24.0), 4600.0, 22.0),
]:
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    lamp = bpy.data.objects.new(name, data)
    scene.collection.objects.link(lamp)
    lamp.location = loc
    point_at(lamp, (0.0, 0.0, 2.5))

camera_data = bpy.data.cameras.new("V928_ReviewCamera")
camera = bpy.data.objects.new("V928_ReviewCamera", camera_data)
scene.collection.objects.link(camera)
scene.camera = camera

views = [
    ("straight_through_side.png", (0.0, -72.0, 7.5), (0.0, 0.0, 2.8), "ORTHO", 58.0),
    ("straight_through_elevated.png", (-38.0, -42.0, 31.0), (0.0, 0.0, 2.2), "PERSP", 48.0),
]

for filename, location, target, camera_type, lens_or_scale in views:
    camera.location = location
    camera_data.type = camera_type
    if camera_type == "ORTHO":
        camera_data.ortho_scale = lens_or_scale
    else:
        camera_data.lens = lens_or_scale
    point_at(camera, target)
    scene.render.filepath = str(OUT_DIR / filename)
    bpy.ops.render.render(write_still=True)
    print("LINE_BOSS_STRAIGHT_THROUGH_RENDER_V928", scene.render.filepath)
