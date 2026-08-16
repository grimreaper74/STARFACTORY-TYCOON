import bpy
import json
import sys
from pathlib import Path
from mathutils import Vector


def world_bounds(obj):
    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    lo = Vector(tuple(min(c[i] for c in corners) for i in range(3)))
    hi = Vector(tuple(max(c[i] for c in corners) for i in range(3)))
    return lo, hi


def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    source = Path(args[0])
    output = Path(args[1])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(source))
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if len(meshes) != 1:
        raise RuntimeError(f"Expected one Meshy mesh, found {len(meshes)}")

    bpy.context.view_layer.objects.active = meshes[0]
    meshes[0].select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.separate(type="LOOSE")
    bpy.ops.object.mode_set(mode="OBJECT")

    parts = []
    for index, obj in enumerate(sorted((o for o in bpy.context.scene.objects if o.type == "MESH"), key=lambda o: o.name)):
        lo, hi = world_bounds(obj)
        center = (lo + hi) * 0.5
        size = hi - lo
        parts.append({
            "index": index,
            "name": obj.name,
            "vertices": len(obj.data.vertices),
            "polygons": len(obj.data.polygons),
            "center": [round(v, 6) for v in center],
            "min": [round(v, 6) for v in lo],
            "max": [round(v, 6) for v in hi],
            "size": [round(v, 6) for v in size],
        })

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"source": str(source), "part_count": len(parts), "parts": parts}, indent=2), encoding="utf-8")
    print(f"LB_LOOSE_PARTS={len(parts)}")
    print(f"LB_LOOSE_PARTS_JSON={output}")


if __name__ == "__main__":
    main()
