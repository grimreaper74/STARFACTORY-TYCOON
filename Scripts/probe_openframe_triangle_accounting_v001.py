"""Measure Blender evaluated and re-imported OpenFrame FBX payload topology.

This evidence-only probe does not save the source blend or edit any Unreal
asset.  It exists because the guarded UE import found a triangle discrepancy
and that fact must be measured before any presentation integration proceeds.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import bpy


ROOT = Path(r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8")
SOURCE = ROOT / "ArtSource/Claude_PressShop_OpenFrameSilhouette_v001"
BLEND = SOURCE / "CA_PTA_OpenFrame_S03S06_v001.blend"
MANIFEST = SOURCE / "openframe_manifest.json"
OUTPUT = ROOT / "Saved/Audits/OneFactory/Press/OpenFrameSilhouetteNative_v001"
RECEIPT = OUTPUT / "openframe_triangle_accounting_v001.json"


def fail(message):
    raise RuntimeError("OPENFRAME_TRIANGLE_ACCOUNTING_V001_FAIL: " + message)


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def tri_metrics(mesh, depsgraph=None):
    mesh.calc_loop_triangles()
    degenerate = 0
    near_degenerate = 0
    min_area = None
    for triangle in mesh.loop_triangles:
        a, b, c = (mesh.vertices[index].co for index in triangle.vertices)
        area = 0.5 * (b - a).cross(c - a).length
        shortest = min((a - b).length, (b - c).length, (c - a).length)
        min_area = area if min_area is None else min(min_area, area)
        if area <= 1.0e-12:
            degenerate += 1
        elif area <= 1.0e-8 or shortest <= 1.0e-5:
            near_degenerate += 1
    return {
        "triangles": len(mesh.loop_triangles),
        "degenerate_area_le_1e-12": degenerate,
        "near_degenerate": near_degenerate,
        "minimum_triangle_area": min_area,
    }


def evaluated_mesh_metrics(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        return tri_metrics(mesh)
    finally:
        evaluated.to_mesh_clear()


def import_fbx_metrics(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(path), use_manual_orientation=False)
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if len(meshes) != 1:
        fail("FBX import expected one mesh for {} but found {}".format(path.name, len(meshes)))
    obj = meshes[0]
    return {"object": obj.name, **evaluated_mesh_metrics(obj)}


def main():
    if not BLEND.is_file() or not MANIFEST.is_file():
        fail("source blend or manifest missing")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    modules = manifest.get("modules", {})
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    source_rows = {}
    for station, module in sorted(modules.items()):
        object_name = module.get("object")
        obj = bpy.data.objects.get(object_name)
        if obj is None or obj.type != "MESH":
            fail("source object missing: {}".format(object_name))
        source_rows[station] = {
            "object": object_name,
            "manifest_evaluated_export_triangles": int(module["evaluated_export_triangles"]),
            "evaluated_blend": evaluated_mesh_metrics(obj),
            "base_mesh": tri_metrics(obj.data),
        }
    fbx_rows = {}
    for station, module in sorted(modules.items()):
        fbx = SOURCE / module["file"]
        if not fbx.is_file():
            fail("source FBX missing: {}".format(station))
        fbx_rows[station] = import_fbx_metrics(fbx)
    result = {
        "$schema": "lineboss/onefactory/press/openframe-silhouette-v001/triangle-accounting/v1",
        "generated_utc": utc_now(),
        "source_blend": str(BLEND),
        "source_manifest": str(MANIFEST),
        "source_blend_modified": False,
        "unreal_assets_modified": False,
        "thresholds": {
            "degenerate_area": 1.0e-12,
            "near_area": 1.0e-8,
            "near_shortest_edge": 1.0e-5,
        },
        "source": source_rows,
        "fbx_reimport": fbx_rows,
    }
    OUTPUT.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("OPENFRAME_TRIANGLE_ACCOUNTING_V001_PASS=" + str(RECEIPT))


if __name__ == "__main__":
    main()
