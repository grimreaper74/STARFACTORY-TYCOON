"""Export one authored PR-005 Blender file into pivot-safe Unreal modules.

The source .blend is read-only. Static geometry and every nearest named mover
subtree become independent FBX assets. Mover locations remain explicit in the
manifest so Unreal can assemble and animate them without exploding the glTF
hierarchy.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector


def args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--module-id", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--root-name", required=True)
    return parser.parse_args(argv)


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]+", "_", value.replace("-", "_"))[:96]


def nearest_mover(obj):
    cursor = obj.parent
    while cursor is not None:
        if "Mover" in cursor.name:
            return cursor
        cursor = cursor.parent
    return None


def renderables(root):
    return [
        obj for obj in root.children_recursive
        if obj.type in {"MESH", "CURVE", "FONT"}
        and not obj.hide_render
        and not obj.name.startswith("Camera")
    ]


def combine_relative(name, sources, pivot_location):
    bpy.ops.object.select_all(action="DESELECT")
    copies = []
    offset = Matrix.Translation(-pivot_location)
    for source in sorted(sources, key=lambda item: item.name):
        duplicate = source.copy()
        duplicate.data = source.data.copy()
        duplicate.animation_data_clear()
        duplicate.parent = None
        duplicate.matrix_world = offset @ source.matrix_world
        bpy.context.collection.objects.link(duplicate)
        bpy.context.view_layer.objects.active = duplicate
        duplicate.select_set(True)
        if duplicate.type != "MESH":
            bpy.ops.object.convert(target="MESH")
            duplicate = bpy.context.object
        duplicate.select_set(False)
        copies.append(duplicate)
    if not copies:
        raise RuntimeError(f"Empty export group {name}")
    for duplicate in copies:
        duplicate.select_set(True)
    bpy.context.view_layer.objects.active = copies[0]
    bpy.ops.object.join()
    result = bpy.context.view_layer.objects.active
    result.name = name
    bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR", center="MEDIAN")
    result.data.validate(clean_customdata=False)
    triangulate = result.modifiers.new(name="UE_Triangulate", type="TRIANGULATE")
    triangulate.quad_method = "BEAUTY"
    triangulate.ngon_method = "BEAUTY"
    bpy.ops.object.modifier_apply(modifier=triangulate.name)
    return result


def bounds_cm(obj):
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    minimum = [min(point[i] for point in points) * 100.0 for i in range(3)]
    maximum = [max(point[i] for point in points) * 100.0 for i in range(3)]
    return {
        "min": [round(value, 3) for value in minimum],
        "max": [round(value, 3) for value in maximum],
        "size": [round(maximum[i] - minimum[i], 3) for i in range(3)],
    }


def export_fbx(obj, path):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.fbx(
        filepath=str(path), use_selection=True, object_types={"MESH"},
        apply_unit_scale=True, apply_scale_options="FBX_SCALE_UNITS",
        axis_forward="-Y", axis_up="Z", use_mesh_modifiers=True,
        mesh_smooth_type="FACE", use_tspace=True, add_leaf_bones=False,
        bake_anim=False, path_mode="AUTO",
    )


def main():
    options = args()
    output = Path(options.output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    root = bpy.data.objects.get(options.root_name)
    if root is None:
        raise RuntimeError(f"Required module root is missing: {options.root_name}")
    meshes = renderables(root)
    if not meshes:
        raise RuntimeError(f"Module root has no renderable descendants: {options.root_name}")
    groups = {"Static": []}
    mover_objects = {}
    for obj in meshes:
        mover = nearest_mover(obj)
        key = mover.name if mover else "Static"
        groups.setdefault(key, []).append(obj)
        if mover:
            mover_objects[key] = mover

    records = []
    for group_name, sources in sorted(groups.items()):
        if not sources:
            continue
        mover = mover_objects.get(group_name)
        pivot = mover.matrix_world.translation.copy() if mover else Vector((0, 0, 0))
        asset_name = safe_name(f"SM_{options.module_id}_{group_name}")
        combined = combine_relative(asset_name, sources, pivot)
        path = output / f"{asset_name}.fbx"
        export_fbx(combined, path)
        records.append({
            "asset_name": asset_name,
            "semantic_group": group_name,
            "is_mover": mover is not None,
            "pivot_blender_m": [round(float(v), 6) for v in pivot],
            "fbx": str(path),
            "source_objects": [obj.name for obj in sorted(sources, key=lambda item: item.name)],
            "material_slots": [
                slot.material.name if slot.material else ""
                for slot in combined.material_slots
            ],
            "bounds_local_cm": bounds_cm(combined),
            "triangles": len(combined.data.polygons),
        })
        bpy.data.objects.remove(combined, do_unlink=True)

    manifest = {
        "schema_version": 1,
        "module_id": options.module_id,
        "module_root": options.root_name,
        "source_blend": bpy.data.filepath,
        "status": "UNREAL_IMPORT_CANDIDATE_NOT_PROMOTED",
        "coordinate_rule": "Blender metres; Unreal location is X,-Y,Z in centimetres",
        "groups": records,
        "group_count": len(records),
        "triangle_count": sum(record["triangles"] for record in records),
    }
    manifest_path = output / "module_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(
        f"LINE_BOSS_PR005_EXPORT_PASS module={options.module_id} "
        f"groups={len(records)} triangles={manifest['triangle_count']} "
        f"manifest={manifest_path}"
    )


if __name__ == "__main__":
    main()
