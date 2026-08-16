"""Write a machine-readable texture/material audit for the currently opened Blender file."""
import bpy
import json
from pathlib import Path

OUT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Saved\Audits\PressTrains\blender_texture_links_v929.json")
OUT.parent.mkdir(parents=True, exist_ok=True)

images = []
for image in bpy.data.images:
    raw = image.filepath or ""
    resolved = bpy.path.abspath(raw) if raw else ""
    images.append({
        "name": image.name,
        "source": image.source,
        "filepath": raw,
        "resolved_filepath": resolved,
        "exists": bool(resolved and Path(resolved).exists()),
        "packed": image.packed_file is not None,
        "size": list(image.size),
    })

materials = []
for material in bpy.data.materials:
    texture_nodes = []
    if material.use_nodes and material.node_tree:
        for node in material.node_tree.nodes:
            if node.type == "TEX_IMAGE":
                texture_nodes.append({
                    "node": node.name,
                    "image": node.image.name if node.image else None,
                    "interpolation": node.interpolation,
                })
    materials.append({
        "name": material.name,
        "use_nodes": material.use_nodes,
        "texture_nodes": texture_nodes,
    })

objects = []
for obj in bpy.data.objects:
    if obj.type != "MESH":
        continue
    objects.append({
        "name": obj.name,
        "materials": [slot.material.name if slot.material else None for slot in obj.material_slots],
        "uv_layers": [uv.name for uv in obj.data.uv_layers],
        "polygons": len(obj.data.polygons),
    })

payload = {
    "blend": bpy.data.filepath,
    "images": images,
    "materials": materials,
    "mesh_objects": objects,
    "summary": {
        "image_count": len(images),
        "missing_external_images": sum(1 for item in images if not item["packed"] and item["source"] == "FILE" and not item["exists"]),
        "packed_images": sum(1 for item in images if item["packed"]),
        "materials": len(materials),
        "mesh_objects": len(objects),
        "meshes_without_uvs": sum(1 for item in objects if not item["uv_layers"]),
        "meshes_without_materials": sum(1 for item in objects if not any(item["materials"])),
    },
}
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print("LINE_BOSS_TEXTURE_AUDIT_V929", OUT)
