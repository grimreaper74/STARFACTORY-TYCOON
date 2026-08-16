"""Emit a compact geometry/material audit for the currently opened Blender file."""
import bpy
import json
import sys
from pathlib import Path
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if len(args) not in (2, 3):
    raise RuntimeError("usage: -- <label> <output.json> [external.glb]")
label, output_path = args[:2]
if len(args) == 3:
    external = Path(args[2])
    if external.suffix.lower() not in (".glb", ".gltf"):
        raise RuntimeError(f"unsupported external format: {external.suffix}")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(external))
output = Path(output_path)
meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH" and not obj.hide_render]
if not meshes:
    raise RuntimeError("candidate has no visible meshes")
points = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
low = Vector(tuple(min(point[i] for point in points) for i in range(3)))
high = Vector(tuple(max(point[i] for point in points) for i in range(3)))
images = [
    {
        "name": image.name,
        "filepath": image.filepath,
        "packed": bool(image.packed_file),
        "size": list(image.size),
    }
    for image in bpy.data.images
    if image.name != "Render Result"
]
payload = {
    "label": label,
    "source": bpy.data.filepath,
    "mesh_count": len(meshes),
    "envelope_m": [round(value, 6) for value in high - low],
    "vertex_count": sum(len(obj.data.vertices) for obj in meshes),
    "polygon_count": sum(len(obj.data.polygons) for obj in meshes),
    "material_count": len({material.name for obj in meshes for material in obj.data.materials if material}),
    "images": images,
    "objects": [
        {
            "name": obj.name,
            "vertices": len(obj.data.vertices),
            "polygons": len(obj.data.polygons),
            "dimensions": [round(value, 6) for value in obj.dimensions],
        }
        for obj in meshes
    ],
}
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print("LINE_BOSS_BLENDER_CANDIDATE_AUDIT_V956", label, payload["polygon_count"])
