"""Render the realised complete runtime train; does not modify the saved Blender asset."""
import bpy
import math
from pathlib import Path
from mathutils import Vector

out = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Saved\ValidationScreenshots\PressShop\Blender_v926\complete_approved_train_runtime.png")
out.parent.mkdir(parents=True, exist_ok=True)

def point_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 2400
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = str(out)
scene.render.film_transparent = False
scene.world.color = (0.008, 0.008, 0.008)

camera_data = bpy.data.cameras.new("RuntimeReviewCamera")
camera = bpy.data.objects.new("RuntimeReviewCamera", camera_data)
scene.collection.objects.link(camera)
camera.location = (0.0, -105.0, 12.0)
camera_data.type = "ORTHO"
camera_data.ortho_scale = 92.0
point_at(camera, (0.0, 0.0, 2.5))
scene.camera = camera

for name, loc, energy, size in [
    ("Key", (-20.0, -35.0, 24.0), 2800.0, 18.0),
    ("Fill", (24.0, -20.0, 15.0), 1800.0, 16.0),
    ("Rim", (0.0, 18.0, 22.0), 2400.0, 20.0),
]:
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    lamp = bpy.data.objects.new(name, data)
    scene.collection.objects.link(lamp)
    lamp.location = loc
    point_at(lamp, (0.0, 0.0, 2.5))

bpy.ops.render.render(write_still=True)
print("LINE_BOSS_COMPLETE_APPROVED_TRAIN_RENDER_V926", out)
