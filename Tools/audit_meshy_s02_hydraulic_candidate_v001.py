"""Read-only Blender audit and review render for the supplied S02 replacement.

It opens the user source without saving it and writes only an audit JSON and
temporary review PNG under Saved/Audits.
"""
import bpy
import hashlib
import json
import math
from pathlib import Path
from mathutils import Vector

SOURCE = Path(r"C:\Users\greg_\Downloads\Meshy_AI_Industrial_Hydraulic__0823071159_texture.blend")
OUT_DIR = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Saved\Audits\PressShopIntegration\MeshyS02HydraulicCandidate_v001")
OUT_JSON = OUT_DIR / "intake_audit.json"
OUT_PNG = OUT_DIR / "review.png"

if not SOURCE.is_file():
    raise RuntimeError("Supplied textured Meshy source is missing")
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH" and not obj.hide_render]
if not meshes:
    raise RuntimeError("No renderable mesh objects in supplied source")

world_points = []
object_rows = []
all_materials = set()
for obj in meshes:
    triangles = sum(len(poly.vertices) - 2 for poly in obj.data.polygons if len(poly.vertices) >= 3)
    points = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    world_points.extend(points)
    for slot in obj.material_slots:
        if slot.material:
            all_materials.add(slot.material.name)
    object_rows.append({
        "name": obj.name,
        "triangles": triangles,
        "vertices": len(obj.data.vertices),
        "materials": [slot.material.name for slot in obj.material_slots if slot.material],
    })

minimum = Vector((min(point.x for point in world_points), min(point.y for point in world_points), min(point.z for point in world_points)))
maximum = Vector((max(point.x for point in world_points), max(point.y for point in world_points), max(point.z for point in world_points)))
centre = (minimum + maximum) * 0.5
size = maximum - minimum
max_size = max(size.x, size.y, size.z)

# Review-only studio: source is never saved after these temporary additions.
for obj in list(bpy.context.scene.objects):
    if obj.type in {"CAMERA", "LIGHT"}:
        bpy.data.objects.remove(obj, do_unlink=True)
world = bpy.context.scene.world or bpy.data.worlds.new("ReviewWorld")
bpy.context.scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.055, 0.07, 0.075, 1.0)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.35

def point_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()

camera_data = bpy.data.cameras.new("ReviewCamera")
camera = bpy.data.objects.new("ReviewCamera", camera_data)
bpy.context.collection.objects.link(camera)
camera.location = centre + Vector((max_size * 1.35, -max_size * 1.45, max_size * 0.95))
point_at(camera, centre + Vector((0.0, 0.0, size.z * 0.05)))
camera_data.lens = 52
bpy.context.scene.camera = camera

for name, offset, energy, colour, size_light in (
    ("Key", (max_size, -max_size, max_size * 1.4), 1200, (1.0, 0.88, 0.72), max_size),
    ("Fill", (-max_size, -max_size * 0.4, max_size * 0.75), 800, (0.55, 0.72, 1.0), max_size * 0.7),
    ("Rim", (max_size * 0.2, max_size, max_size), 1000, (1.0, 1.0, 1.0), max_size * 0.8),
):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size_light
    data.color = colour
    light = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(light)
    light.location = centre + Vector(offset)
    point_at(light, centre)

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1200
scene.render.resolution_y = 1200
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = str(OUT_PNG)
scene.render.film_transparent = False
OUT_DIR.mkdir(parents=True, exist_ok=True)
bpy.ops.render.render(write_still=True)

digest = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
OUT_JSON.write_text(json.dumps({
    "status": "PASS__READ_ONLY_MESHY_S02_HYDRAULIC_INTAKE",
    "source": str(SOURCE),
    "source_sha256": digest,
    "source_bytes": SOURCE.stat().st_size,
    "mesh_object_count": len(meshes),
    "triangles": sum(row["triangles"] for row in object_rows),
    "world_bounds_m": {"min": [round(value, 4) for value in minimum], "max": [round(value, 4) for value in maximum], "size": [round(value, 4) for value in size]},
    "materials": sorted(all_materials),
    "images": [{"name": image.name, "filepath": image.filepath, "packed": image.packed_file is not None, "size": list(image.size)} for image in bpy.data.images],
    "objects": sorted(object_rows, key=lambda row: row["triangles"], reverse=True),
    "review_render": str(OUT_PNG),
    "source_saved": False,
}, indent=2), encoding="utf-8")
print("MESHY_S02_HYDRAULIC_INTAKE_PASS")
