"""Independent clean-FBX audit for PR-004 PackagingRig v004.

Runs in a factory-startup Blender process and trusts neither the build scene nor
its in-memory meshes.  This is a technical source gate only; Unreal fixed-camera
visual, collision, hierarchy and motion gates remain mandatory.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path

import bpy


REPO = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
ROOT = REPO / "SourceAssets/PR004/PackagingRig_v004"
MANIFEST = ROOT / "pr004_packaging_rig_candidate_v004_manifest.json"
SOURCE_MANIFEST = REPO / "SourceAssets/PR004/PackagingRig_v003/pr004_packaging_rig_candidate_v003_manifest.json"
AUDIT = REPO / "Saved/Audits/pr004_packaging_rig_candidate_v004_independent_fbx_uv_audit.json"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for collection in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.images):
        for block in list(collection):
            if block.users == 0:
                collection.remove(block)


def angle_delta(actual, expected):
    return abs((actual - expected + 180.0) % 360.0 - 180.0)


def scalar_props(obj):
    return {key: obj[key] for key in obj.keys()
            if key != "_RNA_UI" and isinstance(obj[key], (str, int, float, bool))}


def values_match(actual, expected):
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
source_by_name = {record["name"]: record for record in source_manifest["modules"]}
results = []

for module in manifest["modules"]:
    path = Path(module["fbx"])
    clear_scene()
    checks = {"fbx_exists": path.is_file(), "sha256_matches_manifest": path.is_file() and sha256(path) == module["fbx_sha256"]}
    if not all(checks.values()):
        results.append({"name": module["name"], "checks": checks, "pass": False})
        continue
    bpy.ops.import_scene.fbx(filepath=str(path), use_custom_props=True)
    objects = list(bpy.context.scene.objects)
    meshes = [obj for obj in objects if obj.type == "MESH"]
    checks["exactly_one_mesh"] = len(meshes) == 1
    checks["no_unexpected_objects"] = len(objects) == 1
    if len(meshes) != 1:
        results.append({"name": module["name"], "checks": checks,
                        "object_types": dict(Counter(obj.type for obj in objects)), "pass": False})
        continue
    obj = meshes[0]
    bounds = [float(value) * 1000.0 for value in obj.dimensions]
    pivot = [float(value) for value in obj.location]
    rotation = [math.degrees(float(value)) for value in obj.rotation_euler]
    bounds_delta = [abs(a - float(e)) for a, e in zip(bounds, module["bounds_mm"])]
    pivot_delta = [abs(a - float(e)) * 1000.0 for a, e in zip(pivot, module["rest_location_m"])]
    rotation_delta = [angle_delta(a, float(e)) for a, e in zip(rotation, module["rest_rotation_deg"])]
    triangles = sum(max(0, len(poly.vertices) - 2) for poly in obj.data.polygons)
    mesh_counts = {"vertices": len(obj.data.vertices), "polygons": len(obj.data.polygons), "triangles": triangles}
    uv_layers = list(obj.data.uv_layers)
    uv = uv_layers[0] if uv_layers else None
    uv_entries = list(uv.data) if uv is not None else []
    finite_uv = bool(uv_entries) and all(math.isfinite(float(entry.uv.x)) and math.isfinite(float(entry.uv.y)) for entry in uv_entries)
    actual_custom = scalar_props(obj)
    expected_custom = module.get("custom_properties", {})
    materials_opaque = bool(obj.material_slots) and all(
        slot.material is not None and float(slot.material.diffuse_color[3]) >= 0.999 for slot in obj.material_slots
    )
    checks.update({
        "expected_v004_name": obj.name == module["name"],
        "identity_import_scale": max(abs(float(value) - 1.0) for value in obj.scale) <= 0.0001,
        "bounds_match_v004_manifest": max(bounds_delta, default=0.0) <= 1.0,
        "pivot_matches_v004_manifest": max(pivot_delta, default=0.0) <= 0.25,
        "rotation_matches_v004_manifest": max(rotation_delta, default=0.0) <= 0.05,
        "mesh_counts_match_v004_manifest": mesh_counts == module["mesh"],
        "custom_metadata_matches_v004_manifest": all(
            key in actual_custom and values_match(actual_custom[key], value) for key, value in expected_custom.items()
        ),
        "one_uv_layer_present": len(uv_layers) == 1,
        "uv0_named_uvmap": uv is not None and uv.name == "UVMap",
        "uv0_covers_every_mesh_loop": len(uv_entries) == len(obj.data.loops) and len(obj.data.loops) > 0,
        "uv0_values_finite": finite_uv,
        "geometry_finite": all(math.isfinite(float(component)) for vertex in obj.data.vertices for component in vertex.co),
        "material_slots_present_and_opaque": materials_opaque,
    })
    if not module["geometry_changed_from_v003"]:
        source = source_by_name[module["source_name"]]
        checks["unchanged_module_bounds_preserved_from_v003"] = max(
            abs(float(a) - float(e)) for a, e in zip(module["bounds_mm"], source["bounds_mm"])
        ) <= 1.0
        checks["unchanged_module_pivot_preserved_from_v003"] = max(
            abs(float(a) - float(e)) * 1000.0 for a, e in zip(module["rest_location_m"], source["rest_location_m"])
        ) <= 0.25
    results.append({
        "name": module["name"], "category": module["category"], "geometry_changed": module["geometry_changed_from_v003"],
        "mesh": mesh_counts, "bounds_mm": [round(value, 3) for value in bounds],
        "deltas": {"bounds_mm": bounds_delta, "pivot_mm": pivot_delta, "rotation_deg": rotation_delta},
        "checks": checks, "pass": all(checks.values()),
    })

changed = [record for record in manifest["modules"] if record["geometry_changed_from_v003"]]
global_checks = {
    "candidate_not_promoted": manifest.get("status") == "CANDIDATE_NOT_PROMOTED",
    "module_count_is_43": len(manifest["modules"]) == 43,
    "changed_module_count_is_28": len(changed) == 28,
    "all_clean_fbx_reimports_pass": all(result["pass"] for result in results),
    "all_uv0_complete": all(result.get("checks", {}).get("uv0_covers_every_mesh_loop") is True and
                              result.get("checks", {}).get("uv0_values_finite") is True for result in results),
    "v003_source_still_exists": (SOURCE_MANIFEST.parent / "LB_PR004_PackagingRig_Candidate_v003.blend").is_file(),
    "no_uasset_in_source_folder": not any(ROOT.glob("*.uasset")),
}
technical_pass = all(global_checks.values())
payload = {
    "$schema": "line-boss/audit/pr004-packaging-rig-v004-independent-fbx-uv/v1",
    "status": "SOURCE_FBX_UV_GATE_PASS__VISUAL_GATE_PENDING__CANDIDATE_NOT_PROMOTED" if technical_pass
              else "SOURCE_FBX_UV_GATE_FAIL__CANDIDATE_NOT_PROMOTED",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "independent_review": True,
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
print(f"LINE_BOSS_PR004_PACKAGING_V004_INDEPENDENT_{'PASS' if technical_pass else 'FAIL'} audit={AUDIT}")
if not technical_pass:
    raise SystemExit(1)
