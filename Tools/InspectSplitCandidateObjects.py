"""Read-only geometry report for explicitly chosen split-source candidates."""
import bpy
import bmesh
import json
import sys
from mathutils import Vector

names = sys.argv[sys.argv.index("--") + 1:]
result = []
for name in names:
    obj = bpy.data.objects.get(name)
    if not obj or obj.type != "MESH":
        result.append({"name": name, "status": "missing"})
        continue
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    low = [min(point[i] for point in points) for i in range(3)]
    high = [max(point[i] for point in points) for i in range(3)]
    mesh = obj.data
    bm = bmesh.new(); bm.from_mesh(mesh)
    nonmanifold = sum(1 for edge in bm.edges if not edge.is_manifold)
    loose = sum(1 for vert in bm.verts if not vert.link_edges)
    bm.free()
    result.append({
        "name": name,
        "dimensions_m": [round(high[i] - low[i], 5) for i in range(3)],
        "vertices": len(mesh.vertices), "polygons": len(mesh.polygons),
        "materials": [slot.material.name if slot.material else None for slot in obj.material_slots],
        "non_manifold_edges": nonmanifold, "loose_vertices": loose,
    })
print(json.dumps(result, indent=2))
