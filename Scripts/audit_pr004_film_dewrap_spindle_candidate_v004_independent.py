"""Independent clean-scene FBX audit for PR-004 film dewrapper v004.

The source .blend and its self-audit are deliberately not trusted.  Blender is
cleared before every import and each exported module is checked against the
manifest.  This script never imports into Unreal or promotes the candidate.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime
import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / "SourceAssets/PR004/FilmDewrapSpindle_v004"
MANIFEST = ROOT / "pr004_film_dewrap_spindle_candidate_v004_manifest.json"
AUDIT = REPO / "Saved/Audits/pr004_film_dewrap_spindle_candidate_v004_independent.json"
RENDER_ROOT = REPO / "Saved/ValidationRenders/PR004/FilmDewrapSpindle_v004"

BOUNDS_TOLERANCE_MM = 1.0
PIVOT_TOLERANCE_MM = 0.25
ROTATION_TOLERANCE_DEG = 0.05
SCALE_TOLERANCE = 0.0001


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for collection in (
        bpy.data.meshes,
        bpy.data.curves,
        bpy.data.cameras,
        bpy.data.lights,
        bpy.data.armatures,
        bpy.data.materials,
        bpy.data.images,
    ):
        for block in list(collection):
            if block.users == 0:
                collection.remove(block)


def world_bounds(obj):
    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    lower = Vector(tuple(min(point[index] for point in corners) for index in range(3)))
    upper = Vector(tuple(max(point[index] for point in corners) for index in range(3)))
    return lower, upper


def angle_delta(actual: float, expected: float) -> float:
    return abs((actual - expected + 180.0) % 360.0 - 180.0)


def scalar_custom_properties(obj) -> dict:
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


def material_record(material) -> dict:
    alpha_values = [float(material.diffuse_color[3])]
    linked_alpha = []
    transparent_nodes = []
    nodes = material.node_tree.nodes if material.use_nodes and material.node_tree else []
    for node in nodes:
        if node.bl_idname in {"ShaderNodeBsdfTransparent", "ShaderNodeHoldout"}:
            transparent_nodes.append(node.name)
        if node.bl_idname == "ShaderNodeBsdfPrincipled":
            alpha = node.inputs.get("Alpha")
            if alpha is not None:
                alpha_values.append(float(alpha.default_value))
                if alpha.is_linked:
                    linked_alpha.append(node.name)
    opaque = all(value >= 0.999 for value in alpha_values) and not linked_alpha and not transparent_nodes
    return {
        "name": material.name,
        "minimum_alpha": round(min(alpha_values), 6),
        "linked_alpha_nodes": linked_alpha,
        "transparent_or_holdout_nodes": transparent_nodes,
        "opaque": opaque,
    }


def import_module(module: dict) -> dict:
    path = Path(module["fbx"])
    clear_scene()
    bpy.ops.import_scene.fbx(filepath=str(path), use_custom_props=True)
    objects = list(bpy.context.scene.objects)
    meshes = [obj for obj in objects if obj.type == "MESH"]
    if len(meshes) != 1:
        return {
            "id": module["id"],
            "expected_name": module["object"],
            "fbx": str(path),
            "object_types": dict(Counter(obj.type for obj in objects)),
            "checks": {"exactly_one_mesh_object": False},
            "pass": False,
        }

    obj = meshes[0]
    lower, upper = world_bounds(obj)
    dimensions_mm = [float(value) * 1000.0 for value in obj.dimensions]
    world_dimensions_mm = [float(upper[i] - lower[i]) * 1000.0 for i in range(3)]
    pivot_m = [float(value) for value in obj.location]
    rotation_deg = [math.degrees(float(value)) for value in obj.rotation_euler]
    scale = [float(value) for value in obj.scale]
    expected_bounds_mm = [float(value) * 10.0 for value in module["local_bounds_xyz_cm"]]
    bounds_delta = [abs(a - b) for a, b in zip(dimensions_mm, expected_bounds_mm)]
    pivot_delta = [abs(value) * 1000.0 for value in pivot_m]
    rotation_delta = [angle_delta(value, 0.0) for value in rotation_deg]

    actual_mesh = {
        "vertices": len(obj.data.vertices),
        "polygons": len(obj.data.polygons),
        "triangles": sum(max(0, len(poly.vertices) - 2) for poly in obj.data.polygons),
    }
    expected_custom = module.get("custom_properties", {})
    actual_custom = scalar_custom_properties(obj)
    missing_custom = sorted(key for key in expected_custom if key not in actual_custom)
    mismatched_custom = {
        key: {"expected": value, "actual": actual_custom.get(key)}
        for key, value in expected_custom.items()
        if key in actual_custom and not values_match(actual_custom[key], value)
    }
    materials = [
        material_record(slot.material)
        for slot in obj.material_slots
        if slot.material is not None
    ]
    pivot_tag = expected_custom.get("pivot_cm")
    try:
        pivot_tag_cm = [float(value) for value in str(pivot_tag).split(",")]
    except (TypeError, ValueError):
        pivot_tag_cm = []
    mover = module["id"] not in {"static", "guards"}
    assembly_pivot_metadata_matches = (
        not mover
        or (
            len(pivot_tag_cm) == 3
            and max(
                abs(actual - float(expected))
                for actual, expected in zip(pivot_tag_cm, module["rest_location_cm"])
            ) <= 0.001
        )
    )
    checks = {
        "exactly_one_mesh_object": True,
        "expected_object_name": obj.name == module["object"],
        "bounds_match_manifest": max(bounds_delta, default=0.0) <= BOUNDS_TOLERANCE_MM,
        "imported_pivot_is_origin": max(pivot_delta, default=0.0) <= PIVOT_TOLERANCE_MM,
        "imported_rotation_is_identity": max(rotation_delta, default=0.0) <= ROTATION_TOLERANCE_DEG,
        "assembly_pivot_metadata_matches_manifest": assembly_pivot_metadata_matches,
        "assembly_rest_transform_is_finite": all(
            math.isfinite(float(value))
            for value in module["rest_location_cm"] + module["rest_rotation_deg"]
        ),
        "unit_scale": max(abs(value - 1.0) for value in scale) <= SCALE_TOLERANCE,
        "positive_finite_bounds": all(value > 0.0 and math.isfinite(value) for value in dimensions_mm),
        "finite_vertices": all(math.isfinite(float(axis)) for vertex in obj.data.vertices for axis in vertex.co),
        "mesh_counts_match_manifest": actual_mesh == module["mesh"],
        "custom_metadata_matches_manifest": not missing_custom and not mismatched_custom,
        "materials_present_and_opaque": bool(materials) and all(item["opaque"] for item in materials),
        "no_unexpected_non_mesh_objects": len(objects) == 1,
    }
    return {
        "id": module["id"],
        "expected_name": module["object"],
        "imported_name": obj.name,
        "fbx": str(path),
        "actual": {
            "pivot_m": [round(value, 6) for value in pivot_m],
            "rotation_deg": [round(value, 5) for value in rotation_deg],
            "scale": [round(value, 6) for value in scale],
            "bounds_mm": [round(value, 3) for value in dimensions_mm],
            "world_aabb_mm": [round(value, 3) for value in world_dimensions_mm],
            "mesh": actual_mesh,
            "custom_properties": actual_custom,
            "materials": materials,
        },
        "deltas": {
            "bounds_mm": [round(value, 4) for value in bounds_delta],
            "pivot_mm": [round(value, 4) for value in pivot_delta],
            "rotation_deg": [round(value, 5) for value in rotation_delta],
        },
        "metadata_differences": {"missing": missing_custom, "mismatched": mismatched_custom},
        "checks": checks,
        "pass": all(checks.values()),
    }


manifest = json.loads(MANIFEST.read_text(encoding="utf-8-sig"))
modules = manifest.get("modules", [])
if not modules:
    raise RuntimeError("Film-dewrapper v004 manifest has no modules")

results = [import_module(module) for module in modules]
fbx_paths = [Path(module["fbx"]) for module in modules]
render_paths = [
    RENDER_ROOT / "pr004_film_dewrap_v004_full_guarded_oblique.png",
    RENDER_ROOT / "pr004_film_dewrap_v004_process_oblique.png",
    RENDER_ROOT / "pr004_film_dewrap_v004_spindle_dancer_close.png",
    RENDER_ROOT / "pr004_film_dewrap_v004_compactor_bale_close.png",
    RENDER_ROOT / "pr004_film_dewrap_v004_near_topdown.png",
    RENDER_ROOT / "pr004_film_dewrap_v004_dancer_high_tension_fault.png",
]
global_checks = {
    "candidate_not_promoted": str(manifest.get("status", "")).endswith("CANDIDATE_NOT_PROMOTED"),
    "eleven_modules": len(modules) == 11,
    "all_asset_ids_unique": len({module["custom_properties"]["line_boss_asset_id"] for module in modules}) == len(modules),
    "all_object_names_unique": len({module["object"] for module in modules}) == len(modules),
    "all_fbx_exist": all(path.is_file() and path.stat().st_size > 0 for path in fbx_paths),
    "folder_fbx_count_matches_manifest": len(list(ROOT.glob("*.fbx"))) == len(modules),
    "all_fbx_versioned_v004": all(path.stem.endswith("_v004") for path in fbx_paths),
    "all_clean_fbx_reimports_pass": all(item["pass"] for item in results),
    "all_six_renders_exist": all(path.is_file() and path.stat().st_size > 10000 for path in render_paths),
    "no_uasset_in_source_folder": not any(ROOT.rglob("*.uasset")),
}

technical_pass = all(global_checks.values())
visual_review = {
    "overall": "FAIL_RELEASE_QUALITY__KEEP_AS_UNPROMOTED_SOURCE_CANDIDATE",
    "mechanical_readability": "PASS_DIRECTIONALLY__spindle, expansion, dancer, stripper, transfer gate, compactor and discharge are separately modular and legible",
    "open_mesh_guarding": "PASS_SOURCE_READABILITY__posts and open mesh are present, though the guarded overview obscures the process more than the Pro sheet",
    "film_path": "PARTIAL__v004 replaces rigid rings with one full-width opaque sheet and wound shell, but the audit material still reads too pale and smooth for dull flexible industrial wrap",
    "dancer_and_tension": "PARTIAL__normal and high-tension film paths differ, but the roller and arm are visually buried and the load response is not sufficiently obvious",
    "compactor_and_discharge": "FAIL_RELEASE_QUALITY__the bale is less spiky than v003 but still reads as a pale crumpled rock/foliage mass rather than dense folded plastic",
    "industrial_fidelity": "PARTIAL__fabrication detail improved, but Blender preview materials remain generic and full-cell PBR parity is unproven",
    "sheet_comparison": "FAIL_PROMOTION__the module does not yet match PR-004-DS-001/PR-004A for process clarity, weathering, full-cell integration or fixed-camera Unreal finish",
}

status = (
    "SOURCE_FBX_GATE_PASS__VISUAL_GATE_FAIL__CANDIDATE_NOT_PROMOTED"
    if technical_pass
    else "SOURCE_FBX_GATE_FAIL__CANDIDATE_NOT_PROMOTED"
)
audit = {
    "$schema": "line-boss/audit/pr004-film-dewrap-spindle-v004-independent/v1",
    "status": status,
    "independent_review": True,
    "method": "INDEPENDENT CLEAN-SCENE FBX REIMPORT AND MANUAL FIXED-RENDER REVIEW",
    "audit_timestamp_local": datetime.now().astimezone().isoformat(),
    "validation_method": "Blender 5.2 cleared the scene and independently re-imported all manifest FBXs, then compared names, bounds, pivots, transforms, mesh counts, metadata and material opacity. Six fresh fixed source renders were reviewed against the authoritative PR-004 sheets.",
    "manifest": str(MANIFEST),
    "module_count": len(modules),
    "tolerances": {
        "bounds_mm": BOUNDS_TOLERANCE_MM,
        "pivot_mm": PIVOT_TOLERANCE_MM,
        "rotation_deg": ROTATION_TOLERANCE_DEG,
        "scale": SCALE_TOLERANCE,
    },
    "global_checks": global_checks,
    "technical_source_pass": technical_pass,
    "module_results": results,
    "renders_reviewed": [str(path) for path in render_paths],
    "visual_review": visual_review,
    "blocking_actions": [
        "Make the dancer arm and roller readable in silhouette and visibly couple them to normal, slack and high-tension film states.",
        "Replace the preview film with a restrained dark-grey thin-sheet PBR treatment that remains opaque and shows controlled creases without cloth fuzz.",
        "Replace the pale rocky bale with a dense folded plastic bundle and prove positive compactor-to-bin discharge.",
        "Assemble the module with the approved powered cradle, robot, cutters and waste stations inside the locked PR-004 footprint.",
        "Run an isolated Unreal material and motion preflight, then capture fixed-camera screenshots against the Pro sheets before any promotion.",
    ],
    "technical_scope_limit": "No Unreal import, runtime animation, collision, interlocks, persistence or level comparison was performed.",
    "promotion": "FORBIDDEN. A clean FBX pass does not establish release quality or runtime correctness.",
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"status": status, "modules": len(modules), "technical_pass": technical_pass, "audit": str(AUDIT)}, indent=2))
