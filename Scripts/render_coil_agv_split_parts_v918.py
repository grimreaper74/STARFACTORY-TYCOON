import bpy, sys
from pathlib import Path

out = Path(sys.argv[sys.argv.index("--") + 1])
out.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 700
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.world.color = (0.025, 0.025, 0.025)

for old in [o for o in scene.objects if o.type in {"CAMERA", "LIGHT"}]:
    bpy.data.objects.remove(old, do_unlink=True)
cam_data = bpy.data.cameras.new("AuditCamera")
cam = bpy.data.objects.new("AuditCamera", cam_data)
scene.collection.objects.link(cam); scene.camera = cam
cam.data.type = "ORTHO"; cam.data.ortho_scale = 3.1
cam.location = (2.7, -3.0, 2.2)

def track(obj, point=(0,0,0)):
    from mathutils import Vector
    obj.rotation_euler = (Vector(point) - obj.location).to_track_quat("-Z", "Y").to_euler()
track(cam)
for location, energy, size in [((3,-4,5),1800,4),((-3,1,3),1100,3)]:
    data=bpy.data.lights.new("Area","AREA"); data.energy=energy; data.shape="DISK"; data.size=size
    lamp=bpy.data.objects.new("Area",data); scene.collection.objects.link(lamp); lamp.location=location; track(lamp)

parts = [o for o in scene.objects if o.type == "MESH"]
for obj in parts:
    mat=bpy.data.materials.new("SplitGuideGrey"); mat.diffuse_color=(0.18,0.5,0.28,1); obj.data.materials.clear(); obj.data.materials.append(mat)
for target in parts:
    for obj in parts: obj.hide_render = obj != target
    scene.render.filepath = str(out / f"{target.name}_isolated.png")
    bpy.ops.render.render(write_still=True)
