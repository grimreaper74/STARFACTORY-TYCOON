"""Independent clean-FBX audit for the PR-004 packaging rig candidate v002.

This deliberately validates the exported exchange assets rather than trusting
the source .blend.  It does not import anything into Unreal and it does not
promote the candidate.
"""

from collections import Counter
from datetime import datetime
from pathlib import Path
import json
import math

import bpy
from mathutils import Vector


REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / "SourceAssets/PR004/PackagingRig_v002"
MANIFEST = ROOT / "pr004_packaging_rig_candidate_v002_manifest.json"
AUDIT = REPO / "Saved/Audits/pr004_packaging_rig_candidate_v002_independent_fbx_visual_audit.json"

BOUNDS_TOLERANCE_MM = 1.0
PIVOT_TOLERANCE_MM = 0.25
ROTATION_TOLERANCE_DEG = 0.05
SCALE_TOLERANCE = 0.0001


def clear_scene():
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


def finite_number(value):
    return math.isfinite(float(value))


def world_bounds(obj):
    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    lower = Vector(tuple(min(point[index] for point in corners) for index in range(3)))
    upper = Vector(tuple(max(point[index] for point in corners) for index in range(3)))
    return lower, upper


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
    linked_alpha = []
    transparent_nodes = []
    for node in material.node_tree.nodes if material.use_nodes and material.node_tree else []:
        if node.bl_idname in {"ShaderNodeBsdfTransparent", "ShaderNodeHoldout"}:
            transparent_nodes.append(node.name)
        if node.bl_idname == "ShaderNodeBsdfPrincipled":
            alpha = node.inputs.get("Alpha")
            if alpha is not None:
                alpha_values.append(float(alpha.default_value))
                if alpha.is_linked:
                    linked_alpha.append(node.name)
            base_color = node.inputs.get("Base Color")
            if base_color is not None and hasattr(base_color.default_value, "__len__"):
                alpha_values.append(float(base_color.default_value[3]))
    opaque = (
        all(value >= 0.999 for value in alpha_values)
        and not linked_alpha
        and not transparent_nodes
    )
    return {
        "name": material.name,
        "diffuse_alpha": round(float(material.diffuse_color[3]), 6),
        "principled_or_diffuse_alpha_min": round(min(alpha_values), 6),
        "linked_alpha_nodes": linked_alpha,
        "transparent_or_holdout_nodes": transparent_nodes,
        "opaque_by_shader_and_alpha": opaque,
    }


def import_module(module):
    path = Path(module["fbx"])
    clear_scene()
    bpy.ops.import_scene.fbx(filepath=str(path), use_custom_props=True)
    all_objects = list(bpy.context.scene.objects)
    meshes = [obj for obj in all_objects if obj.type == "MESH"]
    if len(meshes) != 1:
        return {
            "expected_name": module["name"],
            "asset_id": module["asset_id"],
            "category": module["category"],
            "fbx": str(path),
            "imported_object_types": dict(Counter(obj.type for obj in all_objects)),
            "checks": {"exactly_one_mesh_object": False},
            "pass": False,
        }

    obj = meshes[0]
    lower, upper = world_bounds(obj)
    local_dimensions_mm = [float(value) * 1000.0 for value in obj.dimensions]
    world_dimensions_mm = [float(upper[index] - lower[index]) * 1000.0 for index in range(3)]
    imported_rotation_deg = [math.degrees(float(value)) for value in obj.rotation_euler]
    expected_bounds = [float(value) for value in module["bounds_mm"]]
    expected_pivot = [float(value) for value in module["rest_location_m"]]
    expected_rotation = [float(value) for value in module["rest_rotation_deg"]]
    actual_pivot = [float(value) for value in obj.location]
    actual_scale = [float(value) for value in obj.scale]
    bounds_delta = [abs(a - e) for a, e in zip(local_dimensions_mm, expected_bounds)]
    pivot_delta_mm = [abs(a - e) * 1000.0 for a, e in zip(actual_pivot, expected_pivot)]
    rotation_delta = [
        wrapped_angle_delta_degrees(a, e)
        for a, e in zip(imported_rotation_deg, expected_rotation)
    ]
    triangles = sum(max(0, len(poly.vertices) - 2) for poly in obj.data.polygons)
    actual_mesh = {
        "vertices": len(obj.data.vertices),
        "polygons": len(obj.data.polygons),
        "triangles": triangles,
    }
    expected_mesh = module["mesh"]
    actual_custom = scalar_custom_properties(obj)
    expected_custom = module.get("custom_properties", {})
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
    finite_vertices = all(
        finite_number(coordinate)
        for vertex in obj.data.vertices
        for coordinate in vertex.co
    )
    finite_transform_and_bounds = all(
        finite_number(value)
        for value in (
            actual_pivot
            + actual_scale
            + imported_rotation_deg
            + list(lower)
            + list(upper)
            + local_dimensions_mm
            + world_dimensions_mm
        )
    )
    checks = {
        "exactly_one_mesh_object": True,
        "expected_object_name": obj.name == module["name"],
        "bounds_match_manifest": max(bounds_delta, default=0.0) <= BOUNDS_TOLERANCE_MM,
        "pivot_matches_manifest": max(pivot_delta_mm, default=0.0) <= PIVOT_TOLERANCE_MM,
        "rotation_matches_manifest": max(rotation_delta, default=0.0) <= ROTATION_TOLERANCE_DEG,
        "unit_scale": max(abs(value - 1.0) for value in actual_scale) <= SCALE_TOLERANCE,
        "positive_nonzero_bounds": all(value > 0.0 for value in local_dimensions_mm),
        "finite_vertices": finite_vertices,
        "finite_transform_and_bounds": finite_transform_and_bounds,
        "mesh_counts_match_manifest": actual_mesh == expected_mesh,
        "custom_metadata_matches_manifest": not missing_custom and not mismatched_custom,
        "material_slots_present_and_opaque": bool(materials) and all(
            item["opaque_by_shader_and_alpha"] for item in materials
        ),
        "no_unexpected_non_mesh_objects": len(all_objects) == 1,
    }
    return {
        "expected_name": module["name"],
        "imported_name": obj.name,
        "asset_id": module["asset_id"],
        "category": module["category"],
        "fbx": str(path),
        "imported_object_types": dict(Counter(item.type for item in all_objects)),
        "actual": {
            "pivot_location_m": [round(value, 6) for value in actual_pivot],
            "rotation_euler_deg": [round(value, 5) for value in imported_rotation_deg],
            "scale": [round(value, 6) for value in actual_scale],
            "bounds_xyz_mm": [round(value, 3) for value in local_dimensions_mm],
            "world_aabb_xyz_mm": [round(value, 3) for value in world_dimensions_mm],
            "mesh": actual_mesh,
            "custom_properties": actual_custom,
            "materials": materials,
        },
        "deltas": {
            "bounds_xyz_mm": [round(value, 4) for value in bounds_delta],
            "pivot_xyz_mm": [round(value, 4) for value in pivot_delta_mm],
            "rotation_xyz_deg": [round(value, 5) for value in rotation_delta],
        },
        "metadata_differences": {
            "missing": missing_custom,
            "mismatched": mismatched_custom,
        },
        "checks": checks,
        "pass": all(checks.values()),
    }


manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
modules = manifest.get("modules", [])
if not modules:
    raise RuntimeError("PR-004 packaging v002 manifest contains no modules")

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
    else:
        module_results.append(import_module(module))

category_counts = Counter(module["category"] for module in modules)
declared_counts = {key: int(value) for key, value in manifest.get("module_counts", {}).items()}
asset_ids = [module["asset_id"] for module in modules]
names = [module["name"] for module in modules]
fbx_paths = [Path(module["fbx"]) for module in modules]
render_paths = [Path(path) for path in manifest.get("validation_renders", [])]
cutoff_local = datetime(2026, 8, 1, 21, 18, 0)
post_cutoff_evidence = [MANIFEST, ROOT / "LB_PR004_PackagingRig_Candidate_v002.blend"] + fbx_paths

wrap_runtime = [module for module in modules if module["category"] == "wrap_runtime"]
wrap_waste = [module for module in modules if module["category"] == "wrap_waste_state"]
band_runtime = [module for module in modules if module["category"] == "band_runtime"]
band_waste = [module for module in modules if module["category"] == "band_waste_state"]
primary_bands = [
    module for module in modules
    if module["category"] == "bands" and "CapturedTail" not in module["name"]
]
captured_tails = [
    module for module in modules
    if module["category"] == "bands" and "CapturedTail" in module["name"]
]

wrap_props = wrap_runtime[0].get("custom_properties", {}) if len(wrap_runtime) == 1 else {}
wrap_waste_props = wrap_waste[0].get("custom_properties", {}) if len(wrap_waste) == 1 else {}
band_props = band_runtime[0].get("custom_properties", {}) if len(band_runtime) == 1 else {}
band_waste_props = band_waste[0].get("custom_properties", {}) if len(band_waste) == 1 else {}
band_rule = manifest.get("band_runtime_rule", "").upper()
wrap_rule = manifest.get("wrap_runtime_rule", "").upper()

contract_checks = {
    "persistent_same_coil_actor_rule": all(
        token in manifest.get("persistent_actor_rule", "").upper()
        for token in ("SAME ACTOR", "PACKAGING CHILDREN", "INDIVIDUALLY")
    ),
    "one_wrap_runtime_profile": len(wrap_runtime) == 1,
    "wrap_runtime_is_flexible_spline_ribbon": (
        wrap_props.get("runtime_template") is True
        and "FLEXIBLE_SPLINE_RIBBON" in wrap_props.get("motion_type", "")
        and "EDGE_CURL" in wrap_props.get("motion_type", "")
        and "PRESERVE_LOCAL_CREASES" in wrap_props.get("fold_memory", "")
    ),
    "wrap_rule_requires_guarded_nip_compaction_and_visible_bin_ejection": all(
        token in wrap_rule for token in ("GUARDED NIP", "COMPACT", "VISIBL", "PLASTIC-ONLY BIN")
    ),
    "one_compacted_plastic_waste_state": len(wrap_waste) == 1,
    "plastic_bale_retains_source_identity_and_is_not_a_roll": (
        "INHERIT_ALL_CONSUMED_WRAP_SECTION_IDS" in wrap_waste_props.get("source_identity_rule", "")
        and "IRREGULAR_FOLDED_BALE_NOT_ROLL" in wrap_waste_props.get("shape_contract", "")
        and "VISIBLE_PLASTIC_ONLY_BIN_ENTRY" in wrap_waste_props.get("clear_accounting_rule", "")
    ),
    "four_primary_bands_and_eight_captured_tails": len(primary_bands) == 4 and len(captured_tails) == 8,
    "primary_bands_require_both_ends_and_controlled_withdrawal": all(
        module.get("custom_properties", {}).get("requires_both_ends_captured") is True
        and module.get("custom_properties", {}).get("motion_type") == "SNIP_THEN_CONTROLLED_SPLINE_WITHDRAWAL"
        for module in primary_bands
    ),
    "captured_tails_retain_kinks_through_winder_feed": all(
        module.get("custom_properties", {}).get("state_visibility") == "SHOW_AFTER_CAPTURE_THROUGH_WINDER_FEED"
        and "RETAIN_OUTER_EDGE_AND_BORE_SET_BENDS_UNTIL_POWERED_WINDER"
        in module.get("custom_properties", {}).get("shape_memory", "")
        for module in captured_tails
    ),
    "band_rule_requires_progressive_winding_and_visible_steel_bin_ejection": all(
        token in band_rule for token in ("RETAINING SET-BENDS", "POWERED WINDER", "PANCAKE", "VISIBL", "STEEL BIN")
    ),
    "one_band_runtime_profile": len(band_runtime) == 1,
    "band_runtime_profile_preserves_kinks_until_guarded_winder": (
        band_props.get("runtime_template") is True
        and band_props.get("motion_type") == "FLEXIBLE_SPLINE_WITH_RESTRAINED_RECOIL"
        and "RETAIN_KINK_CONTROL_POINTS" in band_props.get("shape_memory", "")
        and "GUARDED_POWERED_WINDER_FEED" in band_props.get("winder_contract", "")
    ),
    "one_compacted_band_pancake_state": len(band_waste) == 1,
    "compacted_band_state_retains_identity_clip_and_visible_bin_accounting": (
        band_waste_props.get("source_identity_rule") == "INHERIT_ORIGINAL_BAND_ID"
        and "STAMPED_CLIP" in band_waste_props.get("tail_containment", "")
        and "VISIBLE_STEEL_BIN_ENTRY" in band_waste_props.get("clear_accounting_rule", "")
    ),
}

global_checks = {
    "candidate_not_promoted": manifest.get("status") == "CANDIDATE_NOT_PROMOTED",
    "manifest_module_counts_match_records": dict(category_counts) == declared_counts,
    "manifest_total_matches_declared_counts": len(modules) == sum(declared_counts.values()),
    "all_asset_ids_unique": len(asset_ids) == len(set(asset_ids)),
    "all_names_unique": len(names) == len(set(names)),
    "all_fbx_paths_unique": len(fbx_paths) == len(set(fbx_paths)),
    "all_manifest_fbx_exist": all(path.exists() and path.stat().st_size > 0 for path in fbx_paths),
    "folder_fbx_count_matches_manifest": len(list(ROOT.glob("*.fbx"))) == len(modules),
    "all_clean_fbx_reimports_pass": all(result.get("pass", False) for result in module_results),
    "all_contract_checks_pass": all(contract_checks.values()),
    "exactly_seven_declared_validation_renders": len(render_paths) == 7,
    "all_declared_validation_renders_exist": all(path.exists() and path.stat().st_size > 0 for path in render_paths),
    "candidate_files_are_at_or_after_requested_cutoff": all(
        path.exists() and datetime.fromtimestamp(path.stat().st_mtime) >= cutoff_local
        for path in post_cutoff_evidence
    ),
    "no_uasset_in_source_candidate_folder": not any(ROOT.rglob("*.uasset")),
}

technical_pass = all(global_checks.values())
result = {
    "$schema": "line-boss/audit/pr004-packaging-rig-v002-independent/v1",
    "status": (
        "SOURCE_FBX_GATE_PASS__VISUAL_GATE_FAIL__CANDIDATE_NOT_PROMOTED"
        if technical_pass
        else "SOURCE_FBX_GATE_FAIL__VISUAL_GATE_FAIL__CANDIDATE_NOT_PROMOTED"
    ),
    "audit_timestamp_local": datetime.now().astimezone().isoformat(timespec="seconds"),
    "requested_candidate_cutoff_local": cutoff_local.isoformat(timespec="seconds"),
    "candidate_evidence_mtimes_local": {
        str(path): datetime.fromtimestamp(path.stat().st_mtime).astimezone().isoformat(timespec="seconds")
        for path in post_cutoff_evidence
        if path.exists()
    },
    "validation_method": (
        "Blender background process cleared the scene and independently re-imported every manifest FBX; "
        "bounds, pivots, transforms, finite geometry, mesh counts, scalar metadata and material opacity were compared. "
        "Seven source renders were then manually inspected against the authoritative PR-004 Pro reference sheets and user corrections."
    ),
    "blender_version": bpy.app.version_string,
    "manifest": str(MANIFEST),
    "audit": str(AUDIT),
    "module_count": len(modules),
    "expected_module_counts": declared_counts,
    "observed_module_counts": dict(category_counts),
    "tolerances": {
        "bounds_mm": BOUNDS_TOLERANCE_MM,
        "pivot_mm": PIVOT_TOLERANCE_MM,
        "rotation_deg": ROTATION_TOLERANCE_DEG,
        "scale": SCALE_TOLERANCE,
    },
    "contract_checks": contract_checks,
    "global_checks": global_checks,
    "all_source_fbx_checks_pass": technical_pass,
    "module_results": module_results,
    "renders_reviewed": [str(path) for path in render_paths],
    "visual_review": {
        "overall": "FAIL_RELEASE_QUALITY__SUBSTANTIAL_V002_IMPROVEMENT__KEEP_AS_SOURCE_CANDIDATE_ONLY",
        "packaged_coil_opacity": "PASS_IN_SOURCE_RENDERS__opaque; prior transparent-coil defect is not visible here",
        "packaged_coil_shape": "PARTIAL__dimensions and square edge silhouette are plausible, but face caps read as perfectly flat circular boards rather than tightly folded industrial wrap",
        "wrap_material": "FAIL_RELEASE_QUALITY__opaque but near-white, fuzzy and cloth/felt-like; needs dull grey polyethylene read, overlapping seams, tape, wrinkles, compression marks and edge-fold detail",
        "wrap_flexibility": "PASS_DIRECTIONALLY__peeled sheet has curl, folds and a believable hanging mass; current thickness/fuzz still makes it read as blanket fabric",
        "bare_coil_shape": "PASS_DIRECTIONALLY__no tyre-like torus silhouette and edge break is restrained",
        "bare_coil_material": "FAIL_RELEASE_QUALITY__barrel is bright speckled/galvanized while wound face and bore read nearly black rubber; needs coherent anisotropic oiled-steel response and subtler layer grooves",
        "bands_intact": "PARTIAL__route and black contrast are legible, but bands/clips are too pristine and geometrically perfect",
        "post_snip_band": "PARTIAL_SOURCE_PROFILE_ONLY__render shows a kinked retained-bend strip rather than a rigid hoop, but no progressive winder-feed animation or robot restraint is demonstrated",
        "compacted_band_coil": "PASS_DIRECTIONALLY__compact clipped pancake state is visible and matches the requested waste concept; bin ejection remains unshown",
        "compacted_plastic_bale": "PARTIAL__not a boulder or perfect roll, but too cuboid/repetitive and still cloth-like; needs denser irregular crushed-film folds, straps/containment and visible ejection to the plastic-only bin",
        "edge_protectors": "FAIL_RELEASE_QUALITY__formed geometry is readable but bright orange, clean and blocky; needs compressed-fibre/cardboard material, scuffs, creases and thinner believable sections",
        "identity_label_and_rfid": "PARTIAL__readable and useful, but over-clean and must be validated at gameplay distance with wear/adhesion detail",
        "reference_gap": "The Pro sheets show a guarded in-cell sequence with cradle, robot, waste bins and actual handoffs. These isolated studio renders do not prove scale, context, animation, collision, interlocks, persistence or fixed-camera readability."
    },
    "blocking_visual_actions_before_unreal_promotion": [
        "Replace the white fuzzy wrap shader/read with dull opaque grey industrial polyethylene and add overlapping seams, taped joints, wrinkles and folded face-cap corners.",
        "Rework the bare coil face/bore material so all exposed surfaces read as oiled steel; reduce near-black rubber appearance and over-strong uniform grooves.",
        "Make the compacted plastic bale less rectangular/repetitive and clearly crushed-film rather than cloth or stacked foam.",
        "Weather and thin the edge protectors, band clips, label and RFID attachment so they match transported 25-30 tonne coils.",
        "Demonstrate the complete same-identity band path: kinked post-snip spline, guarded winder feed, progressive straightening, clipped pancake and visible steel-bin drop.",
        "Demonstrate the complete plastic path: vacuum peel, guarded nip/compaction, irregular bale and visible plastic-only-bin drop.",
        "After material fixes, run isolated Unreal import/runtime, collision/interlock/persistence and fresh PR-004 fixed-camera comparisons."
    ],
    "technical_scope_limit": "No Unreal import, runtime animation, collision, interlock, persistence or promotion was performed.",
    "promotion": "FORBIDDEN. Passing clean FBX re-import checks does not establish release quality or runtime correctness."
}

AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(result, indent=2), encoding="utf-8")
print(
    "LINE_BOSS_PR004_PACKAGING_V002_INDEPENDENT_AUDIT_"
    + ("SOURCE_PASS_VISUAL_FAIL" if technical_pass else "SOURCE_FAIL_VISUAL_FAIL")
    + f" modules={len(modules)} audit={AUDIT}"
)
