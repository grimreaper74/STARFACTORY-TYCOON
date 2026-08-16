"""Read-only geometry inventory for the Train A hybrid Meshy evaluation."""
import bpy
import json
import sys
from collections import Counter
from pathlib import Path
from mathutils import Vector


def argv_after_dash():
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def world_bounds(obj):
    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    lo = [min(c[i] for c in corners) for i in range(3)]
    hi = [max(c[i] for c in corners) for i in range(3)]
    return lo, hi


def audit_blend(path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    rows = []
    for obj in bpy.data.objects:
        if obj.type not in {"MESH", "CURVE", "FONT"}:
            continue
        lo, hi = world_bounds(obj)
        rows.append({
            "name": obj.name,
            "type": obj.type,
            "parent": obj.parent.name if obj.parent else None,
            "collections": [c.name for c in obj.users_collection],
            "bounds_min": lo,
            "bounds_max": hi,
            "dimensions": list(obj.dimensions),
            "vertices": len(obj.data.vertices) if obj.type == "MESH" else None,
            "polygons": len(obj.data.polygons) if obj.type == "MESH" else None,
            "materials": [s.material.name if s.material else None for s in obj.material_slots],
            "hidden_render": obj.hide_render,
        })
    return {
        "kind": "blend",
        "path": str(path),
        "objects": rows,
        "object_count": len(rows),
        "collection_counts": dict(Counter(c for row in rows for c in row["collections"])),
    }


def audit_glb(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(path))
    rows = []
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        lo, hi = world_bounds(obj)
        rows.append({
            "name": obj.name,
            "bounds_min": lo,
            "bounds_max": hi,
            "dimensions": list(obj.dimensions),
            "vertices": len(obj.data.vertices),
            "polygons": len(obj.data.polygons),
            "materials": [s.material.name if s.material else None for s in obj.material_slots],
        })
    all_lo = [min(row["bounds_min"][i] for row in rows) for i in range(3)]
    all_hi = [max(row["bounds_max"][i] for row in rows) for i in range(3)]
    return {
        "kind": "glb",
        "path": str(path),
        "objects": rows,
        "object_count": len(rows),
        "bounds_min": all_lo,
        "bounds_max": all_hi,
        "dimensions": [all_hi[i] - all_lo[i] for i in range(3)],
        "vertices": sum(row["vertices"] for row in rows),
        "polygons": sum(row["polygons"] for row in rows),
    }


args = argv_after_dash()
if len(args) != 3:
    raise SystemExit("usage: blender -b --python script.py -- TRAIN_A.blend MESHY.glb OUT.json")
blend_path, glb_path, out_path = map(Path, args)
payload = {"train_a": audit_blend(blend_path), "meshy_press": audit_glb(glb_path)}
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({
    "output": str(out_path),
    "train_objects": payload["train_a"]["object_count"],
    "meshy_objects": payload["meshy_press"]["object_count"],
    "meshy_dimensions": payload["meshy_press"]["dimensions"],
    "meshy_polygons": payload["meshy_press"]["polygons"],
}, indent=2))
