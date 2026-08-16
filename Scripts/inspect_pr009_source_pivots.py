import bpy
import json

names = [
    "PR009_M08_SeparatorPicker_01",
    "PR009_M02_GantryBridge_01",
    "PR009_M01_InfeedRoll_01",
]
records = []
for name in names:
    obj = bpy.data.objects[name]
    world_corners = [obj.matrix_world @ __import__("mathutils").Vector(corner) for corner in obj.bound_box]
    records.append({
        "name": name,
        "object_location_m": list(obj.location),
        "world_translation_m": list(obj.matrix_world.translation),
        "mesh_local_bound_min_m": [min(c[index] for c in obj.bound_box) for index in range(3)],
        "mesh_local_bound_max_m": [max(c[index] for c in obj.bound_box) for index in range(3)],
        "world_bound_min_m": [min(c[index] for c in world_corners) for index in range(3)],
        "world_bound_max_m": [max(c[index] for c in world_corners) for index in range(3)],
    })
print("PR009_SOURCE_PIVOT_JSON=" + json.dumps(records, separators=(",", ":")))
