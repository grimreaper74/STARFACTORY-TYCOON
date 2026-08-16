"""Validate the PR-004 removable packaged-coil rig candidate v001.

Run with Blender 5.2 in background mode.  Every FBX listed in the source
manifest is re-imported independently.  The gate checks scale/bounds, exported
pivots, mesh counts, scalar custom metadata, material opacity and module counts.

This is deliberately a source-asset gate only.  In particular, the presence of
the runtime band spline profile and its metadata does not prove that Unreal has
implemented or animated the band-removal sequence.
"""

from collections import Counter
from pathlib import Path
import json
import math

import bpy
from mathutils import Vector


REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / "SourceAssets/PR004/PackagingRig"
MANIFEST = ROOT / "pr004_packaging_rig_candidate_v001_manifest.json"
AUDIT = REPO / "Saved/Audits/pr004_packaging_rig_candidate_v001_fbx_validation.json"

BOUNDS_TOLERANCE_MM = 1.0
PIVOT_TOLERANCE_MM = 0.25
ROTATION_TOLERANCE_DEG = 0.05
SCALE_TOLERANCE = 0.0001


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for collection in (bpy.data.meshes, bpy.data.curves, bpy.data.cameras, bpy.data.lights):
        for block in list(collection):
            if block.users == 0:
                collection.remove(block)


def import_single_fbx(path):
    """Import one module and return its sole mesh object."""
    clear_scene()
    bpy.ops.import_scene.fbx(filepath=str(path), use_custom_props=True)
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if len(meshes) != 1:
        raise RuntimeError(f"Expected one mesh in {path.name}; imported {len(meshes)}")
    return meshes[0]


def world_bounds(obj):
    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    lower = Vector(tuple(min(point[index] for point in corners) for index in range(3)))
    upper = Vector(tuple(max(point[index] for point in corners) for index in range(3)))
    return lower, upper


def rotation_degrees(obj):
    return [math.degrees(value) for value in obj.rotation_euler]


def wrapped_angle_delta_degrees(actual, expected):
    return abs((actual - expected + 180.0) % 360.0 - 180.0)


def scalar_custom_properties(obj):
    values = {}
    for key in obj.keys():
        if key == "_RNA_UI":
            continue
        value = obj[key]
        if isinstance(value, (str, int, float, bool)):
            values[key] = value
    return values


def values_match(actual, expected):
    if isinstance(expected, bool):
        return bool(actual) == expected
    if isinstance(expected, (int, float)) and not isinstance(expected, bool):
        try:
            return abs(float(actual) - float(expected)) <= 0.0001
        except (TypeError, ValueError):
            return False
    return actual == expected


def material_record(material):
    alpha_values = [float(material.diffuse_color[3])]
    alpha_inputs = []
    transparent_nodes = []
    if material.use_nodes and material.node_tree:
        for node in material.node_tree.nodes:
            if node.bl_idname in {"ShaderNodeBsdfTransparent", "ShaderNodeHoldout"}:
                transparent_nodes.append(node.name)
            if node.bl_idname == "ShaderNodeBsdfPrincipled":
                alpha = node.inputs.get("Alpha")
                if alpha is not None:
                    alpha_values.append(float(alpha.default_value))
                    alpha_inputs.append({
                        "node": node.name,
                        "value": round(float(alpha.default_value), 6),
                        "linked": bool(alpha.is_linked),
                    })
                base_color = node.inputs.get("Base Color")
                if base_color is not None and hasattr(base_color.default_value, "__len__"):
                    alpha_values.append(float(base_color.default_value[3]))
    opaque = (
        all(value >= 0.999 for value in alpha_values)
        and not transparent_nodes
        and not any(item["linked"] for item in alpha_inputs)
    )
    return {
        "name": material.name,
        "diffuse_alpha": round(float(material.diffuse_color[3]), 6),
        "surface_render_method": getattr(material, "surface_render_method", None),
        "principled_alpha_inputs": alpha_inputs,
        "transparent_or_holdout_nodes": transparent_nodes,
        "opaque_by_shader_and_alpha": opaque,
    }


def imported_record(obj):
    lower, upper = world_bounds(obj)
    # The source manifest records Blender object dimensions in the object's
    # authored local frame.  Keep rotated world AABB dimensions separately for
    # placement diagnostics; comparing those to the local-frame contract would
    # incorrectly fail 90/270-degree modules.
    dimensions_mm = [value * 1000.0 for value in obj.dimensions]
    world_dimensions_mm = [(upper[index] - lower[index]) * 1000.0 for index in range(3)]
    return {
        "imported_name": obj.name,
        "pivot_location_m": [round(value, 6) for value in obj.location],
        "rotation_euler_deg": [round(value, 5) for value in rotation_degrees(obj)],
        "scale": [round(value, 6) for value in obj.scale],
        "bounds_min_m": [round(value, 6) for value in lower],
        "bounds_max_m": [round(value, 6) for value in upper],
        "bounds_xyz_mm": [round(value, 3) for value in dimensions_mm],
        "world_aabb_xyz_mm": [round(value, 3) for value in world_dimensions_mm],
        "vertices": len(obj.data.vertices),
        "polygons": len(obj.data.polygons),
        "triangles": sum(max(0, len(poly.vertices) - 2) for poly in obj.data.polygons),
        "custom_properties": scalar_custom_properties(obj),
        "materials": [
            material_record(slot.material)
            for slot in obj.material_slots
            if slot.material is not None
        ],
    }


def compare_module(module, imported):
    expected_bounds = module["bounds_mm"]
    actual_bounds = imported["bounds_xyz_mm"]
    bounds_deltas = [abs(actual - expected) for actual, expected in zip(actual_bounds, expected_bounds)]

    expected_pivot = module["rest_location_m"]
    actual_pivot = imported["pivot_location_m"]
    pivot_deltas_mm = [abs(actual - expected) * 1000.0 for actual, expected in zip(actual_pivot, expected_pivot)]

    expected_rotation = module["rest_rotation_deg"]
    actual_rotation = imported["rotation_euler_deg"]
    rotation_deltas = [
        wrapped_angle_delta_degrees(actual, expected)
        for actual, expected in zip(actual_rotation, expected_rotation)
    ]

    expected_custom = module.get("custom_properties", {})
    actual_custom = imported["custom_properties"]
    missing_custom = sorted(key for key in expected_custom if key not in actual_custom)
    mismatched_custom = {
        key: {"expected": value, "actual": actual_custom.get(key)}
        for key, value in expected_custom.items()
        if key in actual_custom and not values_match(actual_custom[key], value)
    }

    expected_mesh = module["mesh"]
    mesh_match = all(imported[key] == expected_mesh[key] for key in ("vertices", "polygons", "triangles"))
    materials = imported["materials"]
    opaque_materials = bool(materials) and all(item["opaque_by_shader_and_alpha"] for item in materials)

    checks = {
        "bounds_match_manifest": max(bounds_deltas, default=0.0) <= BOUNDS_TOLERANCE_MM,
        "pivot_matches_manifest": max(pivot_deltas_mm, default=0.0) <= PIVOT_TOLERANCE_MM,
        "rotation_matches_manifest": max(rotation_deltas, default=0.0) <= ROTATION_TOLERANCE_DEG,
        "unit_scale": max(abs(value - 1.0) for value in imported["scale"]) <= SCALE_TOLERANCE,
        "mesh_counts_match_manifest": mesh_match,
        "custom_metadata_matches_manifest": not missing_custom and not mismatched_custom,
        "material_slots_present_and_opaque": opaque_materials,
    }
    return {
        "expected_name": module["name"],
        "asset_id": module["asset_id"],
        "category": module["category"],
        "fbx": module["fbx"],
        "expected": {
            "pivot_location_m": expected_pivot,
            "rotation_euler_deg": expected_rotation,
            "bounds_xyz_mm": expected_bounds,
            "mesh": expected_mesh,
            "custom_properties": expected_custom,
        },
        "imported": imported,
        "deltas": {
            "bounds_xyz_mm": [round(value, 4) for value in bounds_deltas],
            "pivot_xyz_mm": [round(value, 4) for value in pivot_deltas_mm],
            "rotation_xyz_deg": [round(value, 5) for value in rotation_deltas],
        },
        "metadata_differences": {
            "missing": missing_custom,
            "mismatched": mismatched_custom,
        },
        "checks": checks,
        "pass": all(checks.values()),
    }


def contains_all(text, tokens):
    text = text.upper()
    return all(token.upper() in text for token in tokens)


if not MANIFEST.exists():
    raise RuntimeError(f"Missing PR-004 packaging manifest: {MANIFEST}")

manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
modules = manifest.get("modules", [])
if not modules:
    raise RuntimeError("Packaging manifest has no modules")

AUDIT.parent.mkdir(parents=True, exist_ok=True)

module_results = []
for module in modules:
    path = Path(module["fbx"])
    if not path.exists():
        module_results.append({
            "expected_name": module["name"],
            "asset_id": module["asset_id"],
            "category": module["category"],
            "fbx": str(path),
            "checks": {"fbx_exists": False},
            "pass": False,
        })
        continue
    obj = import_single_fbx(path)
    module_results.append(compare_module(module, imported_record(obj)))

observed_counts = Counter(module["category"] for module in modules)
expected_counts = manifest.get("module_counts", {})
primary_bands = [module for module in modules if module["category"] == "bands" and "CapturedTail" not in module["name"]]
captured_tails = [module for module in modules if module["category"] == "bands" and "CapturedTail" in module["name"]]
runtime_profiles = [module for module in modules if module["category"] == "band_runtime"]
runtime_profile = runtime_profiles[0] if len(runtime_profiles) == 1 else None

band_rule = manifest.get("band_runtime_rule", "")
runtime_properties = runtime_profile.get("custom_properties", {}) if runtime_profile else {}
primary_properties = [module.get("custom_properties", {}) for module in primary_bands]
tail_properties = [module.get("custom_properties", {}) for module in captured_tails]

band_rule_checks = {
    "intact_band_is_tensioned_closed_packaging_child": (
        len(primary_bands) == 4
        and all(props.get("packaging_child") is True for props in primary_properties)
    ),
    "both_cut_ends_must_be_captured_before_snip": (
        len(primary_bands) == 4
        and all(props.get("requires_both_ends_captured") is True for props in primary_properties)
        and len(captured_tails) == 8
    ),
    "snip_opens_loop_instead_of_preserving_coil_shape": contains_all(
        band_rule, ("AT SNIP", "OPEN THE CLOSED LOOP")
    ),
    "post_snip_band_is_flexible_not_rigid": (
        len(runtime_profiles) == 1
        and "FLEXIBLE_SPLINE" in runtime_properties.get("motion_type", "")
        and "RIGID" not in runtime_properties.get("motion_type", "")
    ),
    "set_bends_at_coil_edges_and_bore_are_retained": (
        contains_all(band_rule, ("SET-BENDS", "COIL-EDGE", "BORE"))
        and "RETAIN_KINK_CONTROL_POINTS" in runtime_properties.get("shape_memory", "")
    ),
    "band_uses_segmented_spline_with_restrained_recoil": (
        contains_all(band_rule, ("SEGMENTED SPLINE", "RESTRAINED RECOIL"))
        and runtime_properties.get("runtime_template") is True
        and runtime_properties.get("forward_axis") == "X"
        and runtime_properties.get("cross_section_mm") == "50x2.4"
    ),
    "robot_withdraws_complete_band_before_hiding": (
        len(primary_bands) == 4
        and all(props.get("motion_type") == "SNIP_THEN_CONTROLLED_SPLINE_WITHDRAWAL" for props in primary_properties)
        and all(props.get("hide_rule") == "ONLY_AFTER_VISIBLE_ENTRY_TO_STEEL_BAND_BIN" for props in primary_properties)
    ),
    "captured_tail_visibility_is_transitional": (
        len(captured_tails) == 8
        and all(props.get("state_visibility") == "SHOW_AFTER_CAPTURE_BEFORE_WITHDRAWAL" for props in tail_properties)
    ),
    "all_band_parts_use_steel_banding_waste_stream": (
        all(props.get("waste_stream") == "STEEL_BANDING" for props in primary_properties + tail_properties)
    ),
}

category_counts_match = dict(observed_counts) == expected_counts
all_module_checks_pass = all(result.get("pass", False) for result in module_results)
asset_ids = [module["asset_id"] for module in modules]
names = [module["name"] for module in modules]
fbx_files = list(ROOT.glob("*.fbx"))
existing_renders = [Path(path) for path in manifest.get("validation_renders", [])]

global_checks = {
    "manifest_is_candidate_not_promoted": manifest.get("status") == "CANDIDATE_NOT_PROMOTED",
    "manifest_module_counts_match_records": category_counts_match,
    "manifest_total_matches_sum_of_declared_category_counts": len(modules) == sum(expected_counts.values()),
    "candidate_fbx_total_matches_manifest_total": len(fbx_files) == len(modules),
    "all_asset_ids_unique": len(asset_ids) == len(set(asset_ids)),
    "all_module_names_unique": len(names) == len(set(names)),
    "all_fbx_reimport_checks_pass": all_module_checks_pass,
    "all_material_slots_opaque": all(
        material["opaque_by_shader_and_alpha"]
        for result in module_results
        for material in result.get("imported", {}).get("materials", [])
    ),
    "all_band_runtime_contract_checks_pass": all(band_rule_checks.values()),
    "persistent_coil_actor_rule_is_explicit": contains_all(
        manifest.get("persistent_actor_rule", ""),
        ("SAME ACTOR", "PACKAGING CHILDREN", "INDIVIDUALLY"),
    ),
    "source_scope_contains_no_uasset": not any(ROOT.rglob("*.uasset")),
    "existing_generator_renders_are_present": bool(existing_renders) and all(
        path.exists() and path.stat().st_size > 0 for path in existing_renders
    ),
}

warnings = []
label_modules = [module for module in modules if module["name"] == "SM_LB_PR004_IdentityLabel_v001"]
if label_modules and label_modules[0]["mesh"]["triangles"] > 10000:
    warnings.append(
        "Identity label is 45,616 triangles for a small flat label; optimize or replace with a decal/material before promotion."
    )
warnings.append(
    "Existing still renders show packaged, partial-wrap and bare states, but do not demonstrate the post-snip flexible band withdrawal."
)
warnings.append(
    "The spline profile and metadata are source-ready; Unreal Blueprint spline deformation, robot pull, bin entry and persistence remain unimplemented and unvalidated."
)

result = {
    "$schema": "line-boss/audit/pr004-packaging-rig-fbx-validation/v1",
    "status": "SOURCE_FBX_GATE_PASS_CANDIDATE_NOT_PROMOTED" if all(global_checks.values()) else "SOURCE_FBX_GATE_FAIL_CANDIDATE_NOT_PROMOTED",
    "validation_method": "Blender 5.2 independent FBX re-import of every manifest module; bounds, pivot, rotation, mesh, metadata, opacity and module-count comparison",
    "manifest": str(MANIFEST),
    "audit": str(AUDIT),
    "blender_version": bpy.app.version_string,
    "module_count": len(modules),
    "expected_module_counts": expected_counts,
    "observed_module_counts": dict(observed_counts),
    "tolerances": {
        "bounds_mm": BOUNDS_TOLERANCE_MM,
        "pivot_mm": PIVOT_TOLERANCE_MM,
        "rotation_deg": ROTATION_TOLERANCE_DEG,
        "scale": SCALE_TOLERANCE,
    },
    "intended_band_runtime_sequence": [
        "INTACT_TENSIONED_BAND_ON_PACKAGED_COIL",
        "BOTH_BAND_ENDS_CAPTURED",
        "BAND_SNIPPED_AND_CLOSED_LOOP_OPENS",
        "FLEXIBLE_SPLINE_STRIP_LOSES_COIL_LOOP_SHAPE_BUT_RETAINS_SET_BENDS_AT_EDGES_AND_BORE",
        "ROBOT_PULLS_COMPLETE_STRIP_INTO_STEEL_BANDING_BIN",
        "BAND_HIDDEN_ONLY_AFTER_VISIBLE_BIN_ENTRY",
    ],
    "band_runtime_rule_from_manifest": band_rule,
    "band_runtime_rule_checks": band_rule_checks,
    "runtime_implementation_status": "CONTRACT_AND_SOURCE_PROFILE_READY__UNREAL_SPLINE_ANIMATION_NOT_IMPLEMENTED_OR_VALIDATED",
    "global_checks": global_checks,
    "all_source_fbx_checks_pass": all(global_checks.values()),
    "module_results": module_results,
    "existing_candidate_renders": [str(path) for path in existing_renders],
    "visual_review_status": "POST_SNIP_WITHDRAWAL_ANIMATION_REQUIRES_FRESH_UNREAL_FIXED_CAMERA_VALIDATION",
    "warnings": warnings,
    "scope_limit": "No generator edit, Unreal import, runtime implementation or asset promotion performed.",
    "promotion": "FORBIDDEN until Unreal import, spline animation, robot/bin handoff, interlocks, persistence and fixed-camera visual gates pass.",
}

AUDIT.write_text(json.dumps(result, indent=2), encoding="utf-8")
print(
    "LINE_BOSS_PR004_PACKAGING_FBX_VALIDATION_"
    + ("PASS" if result["all_source_fbx_checks_pass"] else "FAIL")
    + f" modules={len(modules)} audit={AUDIT}"
)
