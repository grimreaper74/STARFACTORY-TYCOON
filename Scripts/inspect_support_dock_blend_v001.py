"""Read-only Blender scene inventory for CR01/MR01 support-dock source files."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import bpy
from mathutils import Vector


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def world_bounds(obj: bpy.types.Object) -> dict | None:
    if not getattr(obj, "bound_box", None):
        return None
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    minimum = [min(point[i] for point in points) for i in range(3)]
    maximum = [max(point[i] for point in points) for i in range(3)]
    return {
        "min_m": [round(value, 6) for value in minimum],
        "max_m": [round(value, 6) for value in maximum],
        "size_m": [round(maximum[i] - minimum[i], 6) for i in range(3)],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_json")
    args = parser.parse_args(bpy.app.driver_namespace.get("argv", []))

    blend = Path(bpy.data.filepath).resolve()
    objects = []
    for obj in sorted(bpy.data.objects, key=lambda item: item.name):
        objects.append(
            {
                "name": obj.name,
                "type": obj.type,
                "location_m": [round(value, 6) for value in obj.matrix_world.translation],
                "rotation_euler_deg": [round(value * 57.295779513, 4) for value in obj.rotation_euler],
                "scale": [round(value, 6) for value in obj.scale],
                "parent": obj.parent.name if obj.parent else None,
                "collections": sorted(collection.name for collection in obj.users_collection),
                "materials": [slot.material.name if slot.material else None for slot in obj.material_slots],
                "library": str(obj.library.filepath) if obj.library else None,
                "bounds": world_bounds(obj),
                "custom_properties": {
                    key: obj[key]
                    for key in sorted(obj.keys())
                    if key != "_RNA_UI" and isinstance(obj[key], (str, int, float, bool))
                },
            }
        )

    mesh_bounds = [entry["bounds"] for entry in objects if entry["type"] == "MESH" and entry["bounds"]]
    scene_bounds = None
    if mesh_bounds:
        minimum = [min(bounds["min_m"][i] for bounds in mesh_bounds) for i in range(3)]
        maximum = [max(bounds["max_m"][i] for bounds in mesh_bounds) for i in range(3)]
        scene_bounds = {
            "min_m": [round(value, 6) for value in minimum],
            "max_m": [round(value, 6) for value in maximum],
            "size_m": [round(maximum[i] - minimum[i], 6) for i in range(3)],
        }

    report = {
        "$schema": "cairnwell/audit/support-dock-blend-inventory-v001/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "blend": str(blend),
        "blend_sha256": sha256(blend),
        "blender_version": bpy.app.version_string,
        "object_count": len(objects),
        "mesh_count": sum(entry["type"] == "MESH" for entry in objects),
        "linked_object_count": sum(bool(entry["library"]) for entry in objects),
        "scene_mesh_bounds": scene_bounds,
        "collections": sorted(collection.name for collection in bpy.data.collections),
        "libraries": sorted(str(library.filepath) for library in bpy.data.libraries),
        "objects": objects,
        "read_only": True,
    }
    output = Path(args.output_json).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({key: report[key] for key in report if key != "objects"}, indent=2))


if __name__ == "__main__":
    import sys

    if "--" in sys.argv:
        bpy.app.driver_namespace["argv"] = sys.argv[sys.argv.index("--") + 1 :]
    else:
        bpy.app.driver_namespace["argv"] = []
    main()
