"""Read-only Blender audit and orthographic views for user-supplied Coil AGV blends."""
import bpy, json, math, sys
from pathlib import Path
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:]
if len(args) != 2:
    raise SystemExit("usage: blender file --python script -- <output-dir> <tag>")
out = Path(args[0]); tag = args[1]; out.mkdir(parents=True, exist_ok=True)
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
if not meshes: raise RuntimeError("no mesh objects")
corners = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
minimum = Vector((min(v.x for v in corners), min(v.y for v in corners), min(v.z for v in corners)))
maximum = Vector((max(v.x for v in corners), max(v.y for v in corners), max(v.z for v in corners)))
centre = (minimum + maximum) * 0.5; dims = maximum - minimum
materials = sorted({m.name for o in meshes for m in o.data.materials if m})
images = []
for image in bpy.data.images:
    images.append({"name": image.name, "size": list(image.size), "packed": bool(image.packed_file), "filepath": image.filepath})

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 900; scene.render.resolution_y = 900; scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.world.color = (0.055, 0.055, 0.055)
for o in scene.objects:
    if o.type in {"CAMERA", "LIGHT"}: bpy.data.objects.remove(o, do_unlink=True)
camera_data = bpy.data.cameras.new("AuditCamera"); camera = bpy.data.objects.new("AuditCamera", camera_data)
scene.collection.objects.link(camera); scene.camera = camera; camera.data.type = "ORTHO"; camera.data.ortho_scale = max(dims) * 1.35
key_data = bpy.data.lights.new("AuditKey", "AREA"); key_data.energy = 1400; key_data.shape = "DISK"; key_data.size = max(dims) * 2
key = bpy.data.objects.new("AuditKey", key_data); scene.collection.objects.link(key)
key.location = centre + Vector((max(dims)*1.4, -max(dims)*1.3, max(dims)*1.8))
fill_data = bpy.data.lights.new("AuditFill", "AREA"); fill_data.energy = 850; fill_data.size = max(dims)*1.5
fill = bpy.data.objects.new("AuditFill", fill_data); scene.collection.objects.link(fill)
fill.location = centre + Vector((-max(dims), max(dims), max(dims)))

def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()

distance = max(dims) * 2.2
views = {
    "front": centre + Vector((0, -distance, dims.z * 0.08)),
    "rear": centre + Vector((0, distance, dims.z * 0.08)),
    "left": centre + Vector((-distance, 0, dims.z * 0.08)),
    "right": centre + Vector((distance, 0, dims.z * 0.08)),
    "oblique": centre + Vector((distance * 0.8, -distance * 0.8, distance * 0.55)),
}
renders = []
for name, location in views.items():
    camera.location = location; look_at(camera, centre)
    scene.render.filepath = str(out / f"{tag}_{name}.png")
    bpy.ops.render.render(write_still=True); renders.append(scene.render.filepath)

payload = {
    "source": bpy.data.filepath, "tag": tag, "mesh_objects": len(meshes),
    "vertices": sum(len(o.data.vertices) for o in meshes), "polygons": sum(len(o.data.polygons) for o in meshes),
    "bounds_min": list(minimum), "bounds_max": list(maximum), "dimensions": list(dims),
    "object_names": [o.name for o in meshes], "materials": materials, "images": images, "renders": renders,
}
(out / f"{tag}_audit.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
print("LINE_BOSS_COIL_AGV_BLEND_AUDIT=" + json.dumps({k: payload[k] for k in ("tag","mesh_objects","vertices","polygons","dimensions")}))
