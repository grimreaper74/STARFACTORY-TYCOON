"""Read-only validation of the PR005 v012 visual-only detail placements."""
import bpy
import json
import os
from mathutils import Vector


def bounds(obj):
    world = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    low = tuple(min(point[i] for point in world) for i in range(3))
    high = tuple(max(point[i] for point in world) for i in range(3))
    return low, high


def overlaps(a, b):
    return all(a[0][i] <= b[1][i] and a[1][i] >= b[0][i] for i in range(3))


scene = bpy.context.scene
details = [obj for obj in scene.objects if obj.name.startswith("SKIN_PR005_v011_")]
clearance = [obj for obj in scene.objects if obj.name.startswith("CLR_")]
moving = [obj for obj in scene.objects if "Mover" in obj.name and obj.name.startswith(("CTX_", "SM_CA_"))]
report = {"candidate_count": len(details), "all_visual_only": True, "all_no_collision": True, "all_no_runtime_export": True, "details": [], "clearance_overlaps": [], "moving_bounds_overlaps": []}
for obj in details:
    entry = {
        "name": obj.name,
        "source_library": obj.get("CW_SourceLibrary"),
        "source_object": obj.get("CW_SourceObject"),
        "collision": obj.get("Collision"),
        "runtime_export": obj.get("ExportToRuntime"),
        "functional": obj.get("Functional"),
        "bounds_m": [[round(value, 4) for value in row] for row in bounds(obj)],
    }
    report["details"].append(entry)
    report["all_visual_only"] &= entry["functional"] is False
    report["all_no_collision"] &= entry["collision"] == "NoCollision"
    report["all_no_runtime_export"] &= entry["runtime_export"] is False
    a = bounds(obj)
    for other in clearance:
        if overlaps(a, bounds(other)):
            report["clearance_overlaps"].append({"detail": obj.name, "clearance": other.name})
    for other in moving:
        if overlaps(a, bounds(other)):
            report["moving_bounds_overlaps"].append({"detail": obj.name, "mover": other.name})
print(json.dumps(report, indent=2))
