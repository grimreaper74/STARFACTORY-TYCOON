"""Read-only Blender/FBX inventory for the PR-009 trace-portal clearance package."""
import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import bpy
from mathutils import Vector

EXPECTED = [
    "PR009_07_LightBar_-1.18", "PR009_07_LightBar_1.18", "PR009_07_TraceBeam",
    "PR009_07_TraceCamera_-0.82_Body", "PR009_07_TraceCamera_-0.82_Lens",
    "PR009_07_TraceCamera_0.0_Body", "PR009_07_TraceCamera_0.0_Lens",
    "PR009_07_TraceCamera_0.82_Body", "PR009_07_TraceCamera_0.82_Lens",
    "PR009_07_TracePost_L", "PR009_07_TracePost_R",
]

def parse_args():
    tokens = __import__("sys").argv
    tokens = tokens[tokens.index("--") + 1:] if "--" in tokens else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("source", "fbx"), required=True)
    parser.add_argument("--input")
    parser.add_argument("--output", required=True)
    return parser.parse_args(tokens)

def rounded(values, digits=9):
    return [round(float(value), digits) for value in values]

def serial(value):
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if hasattr(value, "to_list"):
        return value.to_list()
    try:
        return [serial(item) for item in value]
    except TypeError:
        return str(value)

def props(owner):
    return {key: serial(owner[key]) for key in sorted(owner.keys()) if key != "_RNA_UI"}

def object_row(obj):
    corners_world = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    lo = [min(point[axis] for point in corners_world) for axis in range(3)]
    hi = [max(point[axis] for point in corners_world) for axis in range(3)]
    local_lo = [min(corner[axis] for corner in obj.bound_box) for axis in range(3)]
    local_hi = [max(corner[axis] for corner in obj.bound_box) for axis in range(3)]
    local_centre = [(local_lo[i] + local_hi[i]) * 0.5 for i in range(3)]
    mesh = obj.data
    material_usage = {}
    for polygon in mesh.polygons:
        name = obj.material_slots[polygon.material_index].material.name if polygon.material_index < len(obj.material_slots) and obj.material_slots[polygon.material_index].material else None
        material_usage[str(name)] = material_usage.get(str(name), 0) + 1
    return {
        "name": obj.name,
        "mesh_data_name": mesh.name,
        "location_m": rounded(obj.location),
        "rotation_euler_rad": rounded(obj.rotation_euler),
        "scale": rounded(obj.scale),
        "dimensions_m": rounded(obj.dimensions),
        "world_bounds_min_m": rounded(lo),
        "world_bounds_max_m": rounded(hi),
        "origin_world_m": rounded(obj.matrix_world.translation),
        "local_geometry_centre_from_origin_m": rounded(local_centre),
        "parent": obj.parent.name if obj.parent else None,
        "collections": sorted(collection.name for collection in obj.users_collection),
        "matrix_world_determinant": round(float(obj.matrix_world.to_3x3().determinant()), 9),
        "vertex_count": len(mesh.vertices),
        "polygon_count": len(mesh.polygons),
        "material_slots": [slot.material.name if slot.material else None for slot in obj.material_slots],
        "material_polygon_usage": material_usage,
        "material_custom_properties": {
            slot.material.name: props(slot.material) for slot in obj.material_slots if slot.material
        },
        "object_custom_properties": props(obj),
        "mesh_custom_properties": props(mesh),
    }

args = parse_args()
if args.mode == "fbx":
    if not args.input:
        raise RuntimeError("--input is required for FBX mode")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    result = bpy.ops.import_scene.fbx(filepath=str(Path(args.input).resolve()),
                                      use_custom_props=True, use_image_search=False,
                                      global_scale=1.0, bake_space_transform=False)
    if "FINISHED" not in result:
        raise RuntimeError(f"FBX import failed: {result}")

mesh_objects = sorted((obj for obj in bpy.data.objects if obj.type == "MESH"), key=lambda obj: obj.name)
rows = [object_row(obj) for obj in mesh_objects]
semantic = [row for row in rows if row["name"] in EXPECTED]
unexpected_meshes = sorted(row["name"] for row in rows if row["name"] not in EXPECTED)
missing_meshes = sorted(set(EXPECTED) - {row["name"] for row in rows})
exact_portal_collections = sorted(
    collection.name for collection in bpy.data.collections
    if {obj.name for obj in collection.objects if obj.type == "MESH"} == set(EXPECTED)
)

if semantic:
    envelope_min = [min(row["world_bounds_min_m"][axis] for row in semantic) for axis in range(3)]
    envelope_max = [max(row["world_bounds_max_m"][axis] for row in semantic) for axis in range(3)]
else:
    envelope_min = envelope_max = [None, None, None]
by_name = {row["name"]: row for row in semantic}
left = by_name.get("PR009_07_TracePost_L")
right = by_name.get("PR009_07_TracePost_R")
clear_opening = (right["world_bounds_min_m"][0] - left["world_bounds_max_m"][0]) if left and right else None

failures = []
if args.mode == "fbx" and (len(mesh_objects) != 11 or missing_meshes or unexpected_meshes):
    failures.append(f"expected exactly 11 semantic FBX meshes; total={len(mesh_objects)} missing={missing_meshes} unexpected={unexpected_meshes}")
if args.mode == "source" and not exact_portal_collections:
    failures.append(f"no source collection contains exactly the 11 intended portal meshes; missing={missing_meshes}")
for row in semantic:
    if any(abs(value - 1.0) > 1e-6 for value in row["scale"]):
        failures.append(f"non-identity object scale: {row['name']} {row['scale']}")
    if any(abs(value) > 1e-6 for value in row["rotation_euler_rad"]):
        failures.append(f"unapplied object rotation: {row['name']} {row['rotation_euler_rad']}")
    if any(abs(value) > 1e-5 for value in row["local_geometry_centre_from_origin_m"]):
        failures.append(f"off-centre component pivot: {row['name']} {row['local_geometry_centre_from_origin_m']}")
    if row["mesh_data_name"] != row["name"]:
        failures.append(f"mesh datablock name is not semantic object name: {row['name']} data={row['mesh_data_name']}")
if clear_opening is None or abs(clear_opening - 2.8) > 1e-5:
    failures.append(f"clear opening is not 2.800 m: {clear_opening}")
if semantic and (abs(envelope_min[1] - 2.945) > 1e-5 or abs(envelope_max[1] - 3.355) > 1e-5):
    failures.append(f"source-Y envelope mismatch: {envelope_min[1]}..{envelope_max[1]}")
centre_y = (envelope_min[1] + envelope_max[1]) * 0.5 if semantic else None
if centre_y is None or abs(centre_y - 3.15) > 1e-5:
    failures.append(f"source-Y centre is not 3.150 m: {centre_y}")

payload = {
    "$schema": "cairnwell/audit/pr009-trace-portal-clearance-blender-inventory-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "mode": args.mode,
    "blender_version": bpy.app.version_string,
    "source_file": bpy.data.filepath if args.mode == "source" else str(Path(args.input).resolve()),
    "scene_units": {"system": bpy.context.scene.unit_settings.system,
                    "scale_length": bpy.context.scene.unit_settings.scale_length,
                    "length_unit": bpy.context.scene.unit_settings.length_unit},
    "all_object_types": {kind: sum(1 for obj in bpy.data.objects if obj.type == kind)
                         for kind in sorted({obj.type for obj in bpy.data.objects})},
    "collections": [{"name": collection.name,
                     "mesh_members": sorted(obj.name for obj in collection.objects if obj.type == "MESH"),
                     "object_count": len(collection.objects)}
                    for collection in sorted(bpy.data.collections, key=lambda item: item.name)],
    "mesh_count": len(mesh_objects),
    "semantic_mesh_count": len(semantic),
    "exact_semantic_portal_collections": exact_portal_collections,
    "expected_semantic_names": EXPECTED,
    "missing_semantic_meshes": missing_meshes,
    "unexpected_meshes": unexpected_meshes,
    "objects": semantic,
    "source_envelope_m": {"min": rounded(envelope_min), "max": rounded(envelope_max),
                          "centre": rounded([(envelope_min[i] + envelope_max[i]) * 0.5 for i in range(3)]) if semantic else None},
    "clear_opening_m": round(clear_opening, 9) if clear_opening is not None else None,
    "identity_component_scales": all(all(abs(value - 1.0) <= 1e-6 for value in row["scale"]) for row in semantic),
    "centred_component_pivots": all(all(abs(value) <= 1e-5 for value in row["local_geometry_centre_from_origin_m"]) for row in semantic),
    "semantic_mesh_datablock_names": all(row["mesh_data_name"] == row["name"] for row in semantic),
    "failures": failures,
    "status": "PASS__NOT_PROMOTED" if not failures else "FAIL__NOT_PROMOTED",
    "promotion_authorized": False,
}
out = Path(args.output).resolve()
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({"mode": args.mode, "status": payload["status"], "mesh_count": len(mesh_objects),
                  "failures": failures, "output": str(out)}, indent=2))
