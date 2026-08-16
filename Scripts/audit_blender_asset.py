"""Emit a compact JSON hierarchy/bounds audit for a Blender asset."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def arguments():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    return parser.parse_args(argv)


def bounds(obj):
    if obj.type != "MESH":
        return None
    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    minimum = [min(point[index] for point in corners) for index in range(3)]
    maximum = [max(point[index] for point in corners) for index in range(3)]
    return {
        "min_m": [round(value, 6) for value in minimum],
        "max_m": [round(value, 6) for value in maximum],
        "size_m": [round(maximum[index] - minimum[index], 6) for index in range(3)],
    }


def main():
    args = arguments()
    bpy.context.view_layer.update()
    objects = []
    for obj in sorted(bpy.context.scene.objects, key=lambda item: item.name):
        objects.append(
            {
                "name": obj.name,
                "type": obj.type,
                "parent": obj.parent.name if obj.parent else None,
                "location_m": [round(value, 6) for value in obj.location],
                "rotation_euler_rad": [round(value, 6) for value in obj.rotation_euler],
                "scale": [round(value, 6) for value in obj.scale],
                "bounds": bounds(obj),
                "materials": [slot.material.name if slot.material else None for slot in obj.material_slots],
                "custom_properties": {
                    key: obj[key]
                    for key in obj.keys()
                    if key != "_RNA_UI" and isinstance(obj[key], (str, int, float, bool))
                },
            }
        )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"blend": bpy.data.filepath, "objects": objects}, indent=2), encoding="utf-8")
    print(f"LINE_BOSS_BLENDER_AUDIT_PASS objects={len(objects)} output={output}")


if __name__ == "__main__":
    main()
