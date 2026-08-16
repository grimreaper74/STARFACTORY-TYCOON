"""Read-only Blender audit of modular service-dock objects and collections."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy


def script_args() -> tuple[Path, Path]:
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    if len(args) != 2:
        raise SystemExit("usage: blender --background --python SCRIPT -- SOURCE.blend OUTPUT.json")
    return Path(args[0]), Path(args[1])


source, output = script_args()
bpy.ops.wm.open_mainfile(filepath=str(source))

objects = []
for obj in sorted(bpy.data.objects, key=lambda item: item.name.casefold()):
    bounds = None
    if obj.type == "MESH":
        bounds = {
            "dimensions_mm": [round(value * 1000.0, 3) for value in obj.dimensions],
            "location_mm": [round(value * 1000.0, 3) for value in obj.location],
        }
    objects.append(
        {
            "name": obj.name,
            "type": obj.type,
            "parent": obj.parent.name if obj.parent else None,
            "collections": sorted(collection.name for collection in obj.users_collection),
            "hidden_viewport": bool(obj.hide_viewport),
            "hidden_render": bool(obj.hide_render),
            "bounds": bounds,
        }
    )

payload = {
    "source": str(source),
    "scene": bpy.context.scene.name,
    "collections": [
        {
            "name": collection.name,
            "objects": sorted(obj.name for obj in collection.objects),
        }
        for collection in sorted(bpy.data.collections, key=lambda item: item.name.casefold())
    ],
    "objects": objects,
}
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(f"Wrote {output} with {len(objects)} objects")
