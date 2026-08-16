"""Read-only mesh inventory for an opened Blender source. Does not save inputs."""
import bpy
import json
from mathutils import Vector

items = []
for obj in sorted(bpy.data.objects, key=lambda item: item.name):
    if obj.type != "MESH":
        continue
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    low = [min(point[i] for point in points) for i in range(3)]
    high = [max(point[i] for point in points) for i in range(3)]
    items.append({
        "name": obj.name,
        "mesh": obj.data.name,
        "dimensions_m": [round(high[i] - low[i], 5) for i in range(3)],
        "vertices": len(obj.data.vertices),
        "polygons": len(obj.data.polygons),
        "materials": [slot.material.name if slot.material else None for slot in obj.material_slots],
    })
print("BEGIN_MESH_INVENTORY")
print(json.dumps(items, indent=2))
print("END_MESH_INVENTORY")
print("INPUT_NOT_SAVED")
