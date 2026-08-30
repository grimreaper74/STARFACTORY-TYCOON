"""Read-only topology audit of the user-selected one-coil Meshy press cell.

Runs in Blender background mode.  It writes an evidence report only; the source
blend is never saved or changed.
"""
import json
from pathlib import Path

import bpy

REPORT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Saved\Audits\PressShopIntegration\hero_press_cell_onecoil_v002_blender_topology_audit.json")


def components(mesh):
    parent = list(range(len(mesh.vertices)))

    def find(value):
        while parent[value] != value:
            parent[value] = parent[parent[value]]
            value = parent[value]
        return value

    def union(left, right):
        left, right = find(left), find(right)
        if left != right:
            parent[right] = left

    for polygon in mesh.polygons:
        values = polygon.vertices
        for value in values[1:]:
            union(values[0], value)
    groups = {}
    for index in range(len(mesh.vertices)):
        groups.setdefault(find(index), []).append(index)
    vertex_group = {vertex: root for root, values in groups.items() for vertex in values}
    rows = {root: {"vertices": values, "polygons": []} for root, values in groups.items()}
    for polygon in mesh.polygons:
        rows[vertex_group[polygon.vertices[0]]]["polygons"].append(polygon)
    result = []
    for row in rows.values():
        vertices = [mesh.vertices[index].co for index in row["vertices"]]
        minimum = [min(vertex[index] for vertex in vertices) for index in range(3)]
        maximum = [max(vertex[index] for vertex in vertices) for index in range(3)]
        material_indices = {}
        for polygon in row["polygons"]:
            material_indices[str(polygon.material_index)] = material_indices.get(str(polygon.material_index), 0) + 1
        result.append({
            "vertices": len(row["vertices"]),
            "triangles": sum(len(polygon.vertices) - 2 for polygon in row["polygons"]),
            "bounds_blender_units": {"min": minimum, "max": maximum, "size": [maximum[index] - minimum[index] for index in range(3)]},
            "material_index_triangles": material_indices,
        })
    return sorted(result, key=lambda item: item["triangles"], reverse=True)


objects = []
for obj in bpy.data.objects:
    if obj.type != "MESH":
        continue
    mesh = obj.data
    objects.append({
        "name": obj.name,
        "triangles": sum(len(polygon.vertices) - 2 for polygon in mesh.polygons),
        "vertices": len(mesh.vertices),
        "materials": [material.name if material else None for material in mesh.materials],
        "components": components(mesh)[:40],
    })
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__READ_ONLY_BLENDER_TOPOLOGY_AUDIT",
    "blend": bpy.data.filepath,
    "objects": objects,
    "source_saved": False,
}, indent=2), encoding="utf-8")
print("PRESSSHOP_HERO_PRESS_CELL_ONECOIL_BLENDER_AUDIT_PASS")
