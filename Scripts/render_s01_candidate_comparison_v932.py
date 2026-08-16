"""Render consistent proof views for one S01 Blender candidate; does not save the source."""
import bpy
import sys
from pathlib import Path
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
label = args[0] if args else Path(bpy.data.filepath).stem
out_dir = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Saved\ValidationScreenshots\SourceAssets\S01Comparison_v932")
out_dir.mkdir(parents=True, exist_ok=True)

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1400
scene.render.resolution_y = 1400
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.world.color = (0.025, 0.025, 0.025)

meshes = [o for o in scene.objects if o.type == "MESH" and not o.hide_render]
points = [o.matrix_world @ Vector(corner) for o in meshes for corner in o.bound_box]
if not points:
    raise RuntimeError("No renderable meshes")
mins = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
maxs = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
center = (mins + maxs) * 0.5
size = maxs - mins
span = max(size.x, size.y, size.z)

def point_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()

# Review floor at model bottom.
bpy.ops.mesh.primitive_plane_add(size=max(20.0, span * 3.0), location=(center.x, center.y, mins.z - 0.015))
floor = bpy.context.object
mat = bpy.data.materials.new("S01_ReviewFloor")
mat.diffuse_color = (0.12, 0.13, 0.14, 1.0)
mat.roughness = 0.8
floor.data.materials.append(mat)

for name, direction, energy, lamp_size in [
    ("Key", Vector((-1.0, -1.0, 1.2)), 2600.0, span * 0.8),
    ("Fill", Vector((1.0, -0.4, 0.7)), 1700.0, span * 0.7),
    ("Rim", Vector((0.2, 1.0, 1.1)), 2300.0, span * 0.8),
]:
    data = bpy.data.lights.new(f"S01_{name}", "AREA")
    data.energy = energy
    data.size = max(2.0, lamp_size)
    lamp = bpy.data.objects.new(f"S01_{name}", data)
    scene.collection.objects.link(lamp)
    lamp.location = center + direction.normalized() * span * 1.8
    point_at(lamp, center)

camera_data = bpy.data.cameras.new("S01_ReviewCamera")
camera = bpy.data.objects.new("S01_ReviewCamera", camera_data)
scene.collection.objects.link(camera)
camera_data.type = "ORTHO"
camera_data.ortho_scale = span * 1.28
scene.camera = camera

views = {
    "front": Vector((0.0, -1.0, 0.18)),
    "side": Vector((1.0, 0.0, 0.18)),
    "elevated": Vector((1.0, -1.0, 0.78)),
}
for view_name, direction in views.items():
    camera.location = center + direction.normalized() * span * 3.0
    point_at(camera, center)
    scene.render.filepath = str(out_dir / f"{label}_{view_name}.png")
    bpy.ops.render.render(write_still=True)

print("LINE_BOSS_S01_COMPARISON_V932", label, list(size), len(meshes), out_dir)
