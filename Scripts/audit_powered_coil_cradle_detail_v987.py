import bpy
import hashlib
import json
import sys
from pathlib import Path
from mathutils import Vector

output = Path(sys.argv[sys.argv.index("--") + 1])

objects = []
for obj in bpy.context.scene.objects:
    if obj.type != "MESH":
        continue
    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    low = Vector(tuple(min(point[i] for point in corners) for i in range(3)))
    high = Vector(tuple(max(point[i] for point in corners) for i in range(3)))
    objects.append({
        "name": obj.name,
        "centre_m": [round(value, 6) for value in ((low + high) * 0.5)],
        "low_m": [round(value, 6) for value in low],
        "high_m": [round(value, 6) for value in high],
        "dimensions_m": [round(value, 6) for value in (high - low)],
        "vertices": len(obj.data.vertices),
        "triangles": sum(len(poly.vertices) - 2 for poly in obj.data.polygons),
        "uv_layers": [layer.name for layer in obj.data.uv_layers],
    })

images = []
for image in bpy.data.images:
    if image.name == "Render Result":
        continue
    row = {
        "name": image.name,
        "size": list(image.size),
        "colorspace": image.colorspace_settings.name,
        "packed": image.packed_file is not None,
        "filepath": image.filepath,
    }
    if image.packed_file:
        data = bytes(image.packed_file.data)
        row["bytes"] = len(data)
        row["sha256"] = hashlib.sha256(data).hexdigest().upper()
        row["magic_hex"] = data[:12].hex().upper()
    images.append(row)

materials = []
for material in bpy.data.materials:
    nodes = []
    links = []
    if material.use_nodes and material.node_tree:
        for node in material.node_tree.nodes:
            nodes.append({
                "name": node.name,
                "type": node.type,
                "image": node.image.name if node.type == "TEX_IMAGE" and node.image else None,
            })
        for link in material.node_tree.links:
            links.append({
                "from_node": link.from_node.name,
                "from_socket": link.from_socket.name,
                "to_node": link.to_node.name,
                "to_socket": link.to_socket.name,
            })
    materials.append({"name": material.name, "nodes": nodes, "links": links})

payload = {
    "source": bpy.data.filepath,
    "objects": objects,
    "images": images,
    "materials": materials,
}
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print("LINE_BOSS_POWERED_COIL_CRADLE_DETAIL_V987", len(objects), len(images))
