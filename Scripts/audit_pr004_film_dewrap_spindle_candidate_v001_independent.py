"""Independent FBX and visual audit for the PR-004 film-dewrapper v001.

Run with Blender in background mode.  The scene is cleared before every FBX
import, so this does not trust the source .blend or the builder self-audit.  It
does not import into Unreal or promote the candidate.
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
ROOT = REPO / "SourceAssets/PR004/FilmDewrapSpindle"
MANIFEST = ROOT / "pr004_film_dewrap_spindle_candidate_v001_manifest.json"
AUDIT = REPO / "Saved/Audits/pr004_film_dewrap_spindle_candidate_v001_independent.json"
RENDER_ROOT = REPO / "Saved/ValidationRenders/PR004/FilmDewrapSpindle_v001"

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
    result = {}
    for key in obj.keys():
        if key == "_RNA_UI":
            continue
        value = obj[key]
        if isinstance(value, (str, int, float, bool)):
            result[key] = value
    return result


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
    # Exported modular meshes deliberately use an origin pivot and identity
    # rotation.  Their authored assembly transform is retained in the manifest
    # and in each mover's pivot_cm metadata; Unreal applies that transform when
    # constructing the component hierarchy.
    expected_pivot_m = [0.0, 0.0, 0.0]
    expected_rotation_deg = [0.0, 0.0, 0.0]
    bounds_delta = [abs(a - b) for a, b in zip(dimensions_mm, expected_bounds_mm)]
    pivot_delta = [abs(a - b) * 1000.0 for a, b in zip(pivot_m, expected_pivot_m)]
    rotation_delta = [angle_delta(a, b) for a, b in zip(rotation_deg, expected_rotation_deg)]

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
            and max(abs(a - float(b)) for a, b in zip(pivot_tag_cm, module["rest_location_cm"])) <= 0.001
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
    raise RuntimeError("Film-dewrapper manifest has no modules")

results = [import_module(module) for module in modules]
fbx_paths = [Path(module["fbx"]) for module in modules]
render_paths = [
    RENDER_ROOT / "pr004_film_dewrap_full_guarded_oblique_v001.png",
    RENDER_ROOT / "pr004_film_dewrap_internal_process_v001.png",
    RENDER_ROOT / "pr004_film_dewrap_spindle_dancer_detail_v001.png",
    RENDER_ROOT / "pr004_film_dewrap_compactor_discharge_detail_v001.png",
    RENDER_ROOT / "pr004_film_dewrap_near_topdown_v001.png",
]
global_checks = {
    "candidate_not_promoted": manifest.get("status") == "CANDIDATE_NOT_PROMOTED",
    "eleven_modules": len(modules) == 11,
    "all_asset_ids_unique": len({module["custom_properties"]["line_boss_asset_id"] for module in modules}) == len(modules),
    "all_object_names_unique": len({module["object"] for module in modules}) == len(modules),
    "all_fbx_exist": all(path.is_file() and path.stat().st_size > 0 for path in fbx_paths),
    "folder_fbx_count_matches_manifest": len(list(ROOT.glob("*.fbx"))) == len(modules),
    "all_clean_fbx_reimports_pass": all(item["pass"] for item in results),
    "all_five_renders_exist": all(path.is_file() and path.stat().st_size > 0 for path in render_paths),
    "no_uasset_in_source_folder": not any(ROOT.rglob("*.uasset")),
}

technical_pass = all(global_checks.values())
visual_review = {
    "overall": "FAIL_RELEASE_QUALITY__KEEP_AS_SOURCE_RIG_PROTOTYPE_ONLY",
    "mechanical_readability": "PASS_DIRECTIONALLY__separate spindle, expansion jaws, dancer, stripper, compactor and discharge are legible",
    "open_mesh_guarding": "PASS_SOURCE_READABILITY__real yellow posts and open black mesh are visible",
    "industrial_fidelity": "FAIL__broad clean boxes, oversized edge radii and uniform materials read as a toy/CAD blockout",
    "film_path": "FAIL_RELEASE_QUALITY__the source strip is bright white, narrow and unnaturally clean; it does not demonstrate dull grey flexible wrap peeling from a full coil under tension",
    "dancer_and_tension": "PARTIAL__mechanism is separated but no motion range, load response or tearing state is visually demonstrated",
    "compactor_and_discharge": "FAIL_PROOF__the camera shows a cabinet and empty bin, not an irregular compacted bale being positively discharged",
    "sheet_comparison": "FAIL__isolated module proportions are usable, but the renders do not yet match the detailed, weathered, near-future industrial finish or full-cell context of PR-004-DS-001",
}

status = (
    "SOURCE_FBX_GATE_PASS__VISUAL_GATE_FAIL__CANDIDATE_NOT_PROMOTED"
    if technical_pass
    else "SOURCE_FBX_GATE_FAIL__CANDIDATE_NOT_PROMOTED"
)
audit = {
    "$schema": "line-boss/audit/pr004-film-dewrap-spindle-v001-independent/v1",
    "status": status,
    "audit_timestamp_local": datetime.now().astimezone().isoformat(),
    "validation_method": "Blender 5.2 background process cleared the scene and independently re-imported each manifest FBX, then compared bounds, pivots, transforms, mesh counts, scalar metadata and material opacity. Five fresh source renders were manually reviewed against PR-004-DS-001 Rev A.",
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
        "Rebuild release housings, guards, fasteners, hydraulics, cable routing, service doors and wear details to the powered-cradle visual benchmark.",
        "Demonstrate full-width dull grey packaging from coil peel through tab clamp, dancer, winding layers, stripping and guarded chute without instantaneous replacement.",
        "Demonstrate dancer extremes, tension/synchronisation stop and torn-fragment state.",
        "Create and visibly eject a dense irregular crushed-film bale into the plastic-only bin.",
        "Assemble with cradle and robot inside the locked 1240 cm flow footprint before any Unreal import.",
    ],
    "technical_scope_limit": "No Unreal import, runtime motion, collision, safety interlock, persistence or fixed-camera level comparison was performed.",
    "promotion": "FORBIDDEN. Clean FBX re-import does not establish release quality or runtime correctness.",
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"status": status, "modules": len(modules), "technical_pass": technical_pass, "audit": str(AUDIT)}, indent=2))
