"""Independent clean-FBX/UV audit for PR-004 PackagingRig v003.

This process clears Blender and reimports every exported FBX.  It verifies the
v003 manifest, complete finite UV0 coverage, preserved v002 bounds/pivots/rest
rotations, opaque material slots, metadata, units and module identity.  This is
a technical source gate only; it cannot promote the candidate or substitute
for Unreal fixed-camera visual review.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import json
import math

import bpy
from mathutils import Vector


REPO = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
ROOT = REPO / "SourceAssets/PR004/PackagingRig_v003"
MANIFEST = ROOT / "pr004_packaging_rig_candidate_v003_manifest.json"
SOURCE_MANIFEST = REPO / "SourceAssets/PR004/PackagingRig_v002/pr004_packaging_rig_candidate_v002_manifest.json"
AUDIT = REPO / "Saved/Audits/pr004_packaging_rig_candidate_v003_independent_fbx_uv_audit.json"

BOUNDS_TOLERANCE_MM = 1.0
PIVOT_TOLERANCE_MM = 0.25
ROTATION_TOLERANCE_DEG = 0.05


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for collection in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.images):
        for block in list(collection):
            if block.users == 0:
                collection.remove(block)


def angle_delta(actual: float, expected: float) -> float:
    return abs((actual - expected + 180.0) % 360.0 - 180.0)


def scalar_props(obj) -> dict:
    return {
        key: obj[key]
        for key in obj.keys()
        if key != "_RNA_UI" and isinstance(obj[key], (str, int, float, bool))
    }


def values_match(actual, expected) -> bool:
    if isinstance(expected, bool):
        return bool(actual) == expected
    if isinstance(expected, (int, float)) and not isinstance(expected, bool):
        try:
            return abs(float(actual) - float(expected)) <= 0.0001
        except (TypeError, ValueError):
            return False
    return actual == expected


manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
source_manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
source_by_name = {module["name"]: module for module in source_manifest["modules"]}
results = []

for module in manifest["modules"]:
    path = Path(module["fbx"])
    clear_scene()
    if not path.is_file():
        results.append({"name": module["name"], "checks": {"fbx_exists": False}, "pass": False})
        continue

    bpy.ops.import_scene.fbx(filepath=str(path), use_custom_props=True)
    objects = list(bpy.context.scene.objects)
    meshes = [obj for obj in objects if obj.type == "MESH"]
    if len(meshes) != 1:
        results.append({
            "name": module["name"],
            "checks": {"exactly_one_mesh": False},
            "object_types": dict(Counter(obj.type for obj in objects)),
            "pass": False,
        })
        continue

    obj = meshes[0]
    expected_source = source_by_name[module["source_name"]]
    actual_bounds = [float(value) * 1000.0 for value in obj.dimensions]
    actual_pivot = [float(value) for value in obj.location]
    actual_rotation = [math.degrees(float(value)) for value in obj.rotation_euler]
    expected_bounds = [float(value) for value in expected_source["bounds_mm"]]
    expected_pivot = [float(value) for value in expected_source["rest_location_m"]]
    expected_rotation = [float(value) for value in expected_source["rest_rotation_deg"]]
    bounds_delta = [abs(a - e) for a, e in zip(actual_bounds, expected_bounds)]
    pivot_delta = [abs(a - e) * 1000.0 for a, e in zip(actual_pivot, expected_pivot)]
    rotation_delta = [angle_delta(a, e) for a, e in zip(actual_rotation, expected_rotation)]

    uv_layers = list(obj.data.uv_layers)
    uv_layer = uv_layers[0] if uv_layers else None
    uv_entries = list(uv_layer.data) if uv_layer is not None else []
    finite_uv = all(
        math.isfinite(float(entry.uv.x)) and math.isfinite(float(entry.uv.y))
        for entry in uv_entries
    )
    mesh_loop_count = len(obj.data.loops)

    actual_custom = scalar_props(obj)
    expected_custom = module.get("custom_properties", {})
    metadata_ok = all(
        key in actual_custom and values_match(actual_custom[key], value)
        for key, value in expected_custom.items()
    )
    triangles = sum(max(0, len(poly.vertices) - 2) for poly in obj.data.polygons)
    mesh_counts = {
        "vertices": len(obj.data.vertices),
        "polygons": len(obj.data.polygons),
        "triangles": triangles,
    }
    materials_opaque = bool(obj.material_slots)
    for slot in obj.material_slots:
        material = slot.material
        if material is None or float(material.diffuse_color[3]) < 0.999:
            materials_opaque = False

    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    geometry_finite = all(math.isfinite(float(coord)) for vertex in obj.data.vertices for coord in vertex.co)
    transform_finite = all(
        math.isfinite(float(value))
        for value in actual_bounds + actual_pivot + actual_rotation + [coord for point in corners for coord in point]
    )

    checks = {
        "fbx_exists": True,
        "exactly_one_mesh": True,
        "expected_v003_name": obj.name == module["name"],
        "bounds_preserved_from_v002": max(bounds_delta, default=0.0) <= BOUNDS_TOLERANCE_MM,
        "pivot_preserved_from_v002": max(pivot_delta, default=0.0) <= PIVOT_TOLERANCE_MM,
        "rotation_preserved_from_v002": max(rotation_delta, default=0.0) <= ROTATION_TOLERANCE_DEG,
        "unit_scale": max(abs(float(value) - 1.0) for value in obj.scale) <= 0.0001,
        "mesh_counts_match_v003_manifest": mesh_counts == module["mesh"],
        "custom_metadata_matches_v003_manifest": metadata_ok,
        "one_uv_layer_present": len(uv_layers) == 1,
        "uv0_named_uvmap": uv_layer is not None and uv_layer.name == "UVMap",
        "uv0_covers_every_mesh_loop": len(uv_entries) == mesh_loop_count and mesh_loop_count > 0,
        "uv0_values_finite": finite_uv and bool(uv_entries),
        "geometry_finite": geometry_finite,
        "transform_finite": transform_finite,
        "material_slots_present_and_opaque": materials_opaque,
        "no_unexpected_objects": len(objects) == 1,
    }
    results.append({
        "name": module["name"],
        "source_name": module["source_name"],
        "asset_id": module["asset_id"],
        "category": module["category"],
        "fbx": str(path),
        "mesh": mesh_counts,
        "uv": {
            "layers": [layer.name for layer in uv_layers],
            "mesh_loops": mesh_loop_count,
            "entries": len(uv_entries),
            "finite": finite_uv,
        },
        "deltas": {
            "bounds_mm": [round(value, 4) for value in bounds_delta],
            "pivot_mm": [round(value, 4) for value in pivot_delta],
            "rotation_deg": [round(value, 5) for value in rotation_delta],
        },
        "checks": checks,
        "pass": all(checks.values()),
    })

category_counts = Counter(module["category"] for module in manifest["modules"])
global_checks = {
    "candidate_not_promoted": manifest.get("status") == "CANDIDATE_NOT_PROMOTED",
    "module_count_is_43": len(manifest["modules"]) == 43,
    "category_counts_match_manifest": dict(category_counts) == manifest["module_counts"],
    "all_clean_fbx_reimports_pass": all(item["pass"] for item in results),
    "all_uv0_complete": all(
        item.get("checks", {}).get("uv0_covers_every_mesh_loop") is True
        and item.get("checks", {}).get("uv0_values_finite") is True
        for item in results
    ),
    "source_v002_package_still_exists": (
        REPO / "SourceAssets/PR004/PackagingRig_v002/LB_PR004_PackagingRig_Candidate_v002.blend"
    ).is_file(),
    "no_uasset_in_source_folder": not any(ROOT.glob("*.uasset")),
}
technical_pass = all(global_checks.values())
payload = {
    "$schema": "line-boss/audit/pr004-packaging-rig-v003-independent-fbx-uv/v1",
    "status": (
        "SOURCE_FBX_UV_GATE_PASS__VISUAL_GATE_PENDING__CANDIDATE_NOT_PROMOTED"
        if technical_pass
        else "SOURCE_FBX_UV_GATE_FAIL__CANDIDATE_NOT_PROMOTED"
    ),
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "independent_review": True,
    "validation_method": (
        "Independent Blender factory-startup process cleared the scene and clean-FBX reimported every v003 module; "
        "v002 bounds, pivots and rest rotations plus v003 identity, finite geometry and complete finite UV0 were checked."
    ),
    "fbx_gate_pass": technical_pass,
    "technical_pass": technical_pass,
    "manifest": str(MANIFEST),
    "source_manifest": str(SOURCE_MANIFEST),
    "module_count": len(results),
    "checks": global_checks,
    "module_results": results,
    "visual_gate": "PENDING_UNREAL_PBR_FIXED_CAMERA_REVIEW",
    "promotion": "FORBIDDEN",
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(
    "LINE_BOSS_PR004_PACKAGING_V003_INDEPENDENT_"
    f"{'PASS' if technical_pass else 'FAIL'} modules={len(results)} audit={AUDIT}"
)
if not technical_pass:
    raise SystemExit(1)
