"""Read-only PR-003 -> PR-004 -> PR-005 geometry and clearance audit.

This script deliberately does not launch Unreal, import assets, move station
anchors, or edit runtime content.  It combines the authoritative station data,
the latest generated population/integration audits, and candidate source-asset
manifests.  Unknown geometry is a blocker rather than an assumed pass.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any, Iterable


REPO = Path(__file__).resolve().parents[1]
OUTPUT = REPO / "Saved" / "Audits" / "pr004_pr005_clearance_v001.json"

PATHS = {
    "anchors": REPO / "Content" / "LineBoss" / "Data" / "press_shop_master_plan_anchors_v001.json",
    "placements": REPO / "Content" / "LineBoss" / "Data" / "press_shop_station_placements_v001.json",
    "pr004_contract": REPO / "Content" / "LineBoss" / "Data" / "pr004_robotic_depack_cell_v001.json",
    "pr005_contract": REPO / "SourceAssets" / "PR005" / "pr005_gameplay_contract_v001.json",
    "front_population": REPO / "Saved" / "Audits" / "press_shop_front_end_population_v002.json",
    "integration": REPO / "Saved" / "Audits" / "press_shop_integration_candidate_v002.json",
    "pr005_level_bounds": REPO / "Saved" / "Audits" / "pr005_unreal_level_bounds_v001.json",
    "coil_v003": REPO / "SourceAssets" / "IndustrialKit" / "MasterCoil" / "master_coil_candidate_v003_manifest.json",
    "saddle_v002": REPO / "SourceAssets" / "IndustrialKit" / "CoilSaddle" / "coil_saddle_candidate_v002_manifest.json",
    "cradle_v001": REPO / "SourceAssets" / "PR004" / "PoweredRestrainedCradle" / "pr004_powered_cradle_candidate_v001_manifest.json",
    "current_coil_audit": REPO / "Saved" / "Audits" / "master_coil_candidate_v002.json",
    "current_saddle_audit": REPO / "Saved" / "Audits" / "coil_saddle_candidate_v001.json",
    "population_script": REPO / "Scripts" / "build_press_shop_front_end_population.py",
}

# Explicit design assumption for this audit.  The PR-004 contract contains
# several 100-150 cm service/standoff requirements but no single authoritative
# inter-station value.  120 cm is therefore tested and labelled as an
# assumption; it is not written back into any design contract.
ASSUMED_INTERSTATION_CLEARANCE_CM = 120.0


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def rounded(value: float) -> float:
    return round(float(value), 3)


def vector(values: Iterable[float]) -> list[float]:
    return [rounded(value) for value in values]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def source_record(path: Path) -> dict[str, Any]:
    return {
        "path": path.relative_to(REPO).as_posix(),
        "exists": path.is_file(),
        "bytes": path.stat().st_size if path.is_file() else None,
        "sha256": sha256(path) if path.is_file() else None,
    }


def aabb_from_center_size(center: list[float], size: list[float]) -> dict[str, list[float]]:
    half = [dimension / 2.0 for dimension in size]
    return {
        "min": [center[index] - half[index] for index in range(len(size))],
        "max": [center[index] + half[index] for index in range(len(size))],
        "size": list(size),
    }


def union_aabbs(aabbs: list[dict[str, list[float]]]) -> dict[str, list[float]]:
    dimensions = len(aabbs[0]["min"])
    minimum = [min(item["min"][axis] for item in aabbs) for axis in range(dimensions)]
    maximum = [max(item["max"][axis] for item in aabbs) for axis in range(dimensions)]
    return {
        "min": minimum,
        "max": maximum,
        "size": [maximum[axis] - minimum[axis] for axis in range(dimensions)],
    }


def transform_aabb_2d(
    local_min: list[float],
    local_max: list[float],
    origin_xy: list[float],
    yaw_degrees: float,
) -> dict[str, list[float]]:
    angle = math.radians(yaw_degrees)
    cosine = math.cos(angle)
    sine = math.sin(angle)
    points = []
    for x in (local_min[0], local_max[0]):
        for y in (local_min[1], local_max[1]):
            points.append(
                [
                    origin_xy[0] + cosine * x - sine * y,
                    origin_xy[1] + sine * x + cosine * y,
                ]
            )
    return union_aabbs([{"min": point, "max": point, "size": [0.0, 0.0]} for point in points])


def aabb_intersection_2d(
    left: dict[str, list[float]], right: dict[str, list[float]]
) -> dict[str, Any]:
    overlap = [
        min(left["max"][axis], right["max"][axis])
        - max(left["min"][axis], right["min"][axis])
        for axis in range(2)
    ]
    intersects = overlap[0] > 0.0 and overlap[1] > 0.0
    return {
        "intersects": intersects,
        "overlap_xy_cm": vector([max(0.0, value) for value in overlap]),
        "overlap_area_cm2": rounded(max(0.0, overlap[0]) * max(0.0, overlap[1])),
    }


def bounds_record(aabb: dict[str, list[float]]) -> dict[str, list[float]]:
    return {key: vector(value) for key, value in aabb.items()}


def station_by_id(anchors: dict[str, Any], station_id: str) -> dict[str, Any]:
    return next(station for station in anchors["stations"] if station["id"] == station_id)


def current_boundary_x(population_script: Path) -> dict[str, Any]:
    source = population_script.read_text(encoding="utf-8")
    fence_matches = re.findall(
        r'add_fence_line\("PR004_PR005Boundary_[^"]+",\s*\((-?\d+(?:\.\d+)?),',
        source,
    )
    gate_match = re.search(
        r'add_interlocked_gate\("PR004_PR005TransferGate",\s*\((-?\d+(?:\.\d+)?),',
        source,
    )
    unique_fence_x = sorted({float(value) for value in fence_matches})
    gate_x = float(gate_match.group(1)) if gate_match else None
    consistent = len(unique_fence_x) == 1 and gate_x == unique_fence_x[0]
    return {
        "fence_x_values_cm": vector(unique_fence_x),
        "transfer_gate_x_cm": rounded(gate_x) if gate_x is not None else None,
        "consistent": consistent,
        "source": population_script.relative_to(REPO).as_posix(),
    }


def main() -> None:
    missing = [path.relative_to(REPO).as_posix() for path in PATHS.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Required audit sources missing: {missing}")

    anchors = load_json(PATHS["anchors"])
    placements = load_json(PATHS["placements"])
    pr004 = load_json(PATHS["pr004_contract"])
    pr005 = load_json(PATHS["pr005_contract"])
    population = load_json(PATHS["front_population"])
    integration = load_json(PATHS["integration"])
    level_bounds = load_json(PATHS["pr005_level_bounds"])
    coil_v003 = load_json(PATHS["coil_v003"])
    saddle_v002 = load_json(PATHS["saddle_v002"])
    cradle_v001 = load_json(PATHS["cradle_v001"])
    current_coil = load_json(PATHS["current_coil_audit"])
    current_saddle = load_json(PATHS["current_saddle_audit"])

    anchor_003 = station_by_id(anchors, "PR-003")
    anchor_004 = station_by_id(anchors, "PR-004")
    anchor_005 = station_by_id(anchors, "PR-005")
    placement_005 = next(station for station in placements["stations"] if station["id"] == "PR-005")

    anchor_checks = {
        "pr004_contract_matches_master_anchor": pr004["facility_anchor"]["world_cm"] == anchor_004["world_cm"],
        "pr005_placement_matches_master_anchor": placement_005["world_origin_cm"] == anchor_005["world_cm"],
        "pr005_integration_matches_placement": integration["station"]["world_origin_cm"] == placement_005["world_origin_cm"],
        "pr005_yaw_maps_local_positive_y_to_world_positive_x": rounded(placement_005["yaw_degrees"]) == -90.0,
        "pr005_material_flow_orientation_audit_pass": integration.get("material_flow_orientation_pass") is True,
        "pr003_population_has_exactly_12_slots": len(population["pr003_slots"]) == anchors["fixed"]["pr003_slot_count"] == 12,
    }

    # PR-003 occupied bounds in the current generated map.  The store coils are
    # yawed 90 degrees; the saddle is unrotated.  Candidate v003/v002 bounds are
    # also evaluated because they are the intended replacements but are not yet
    # promoted into that map.
    slots = population["pr003_slots"]
    distinct_flow_x = sorted({float(slot["world_cm"][0]) for slot in slots})
    distinct_across_y = sorted({float(slot["world_cm"][1]) for slot in slots})

    current_coil_size = current_coil["bounds_cm"]["size"]
    current_coil_world_xy = [current_coil_size[1], current_coil_size[0]]
    current_saddle_xy = current_saddle["bounds_cm"]["size"][:2]
    target_coil_xyz = [value / 10.0 for value in coil_v003["source_bounds_xyz_mm"]]
    target_coil_world_xy = [target_coil_xyz[1], target_coil_xyz[0]]
    target_saddle_xyz = [value / 10.0 for value in saddle_v002["source_bounds_xyz_mm"]]
    target_saddle_xy = target_saddle_xyz[:2]

    def store_union(coil_xy: list[float], saddle_xy: list[float]) -> dict[str, list[float]]:
        occupied = []
        for slot in slots:
            center = [float(slot["world_cm"][0]), float(slot["world_cm"][1])]
            occupied.append(aabb_from_center_size(center, coil_xy))
            occupied.append(aabb_from_center_size(center, saddle_xy))
        return union_aabbs(occupied)

    pr003_current = store_union(current_coil_world_xy, current_saddle_xy)
    pr003_target = store_union(target_coil_world_xy, target_saddle_xy)

    # Proposed centred PR-004 cell envelope, exactly as currently recorded in
    # the design-lock contract.  This is a proposed outer cell/fence envelope,
    # not proven built geometry.
    pr004_anchor_xy = [float(value) for value in anchor_004["world_cm"][:2]]
    pr004_size_xy = [
        float(pr004["facility_anchor"]["world_footprint_cm"]["flow_x"]),
        float(pr004["facility_anchor"]["world_footprint_cm"]["across_y"]),
    ]
    pr004_envelope = aabb_from_center_size(pr004_anchor_xy, pr004_size_xy)

    # PR-005 conservative gameplay envelope after its corrected -90 degree
    # station rotation.
    pr005_local_center = pr005["footprint"]["centre"][:2]
    pr005_local_half = pr005["footprint"]["half_extent"][:2]
    pr005_local_min = [pr005_local_center[i] - pr005_local_half[i] for i in range(2)]
    pr005_local_max = [pr005_local_center[i] + pr005_local_half[i] for i in range(2)]
    pr005_origin_xy = [float(value) for value in placement_005["world_origin_cm"][:2]]
    pr005_yaw = float(placement_005["yaw_degrees"])
    pr005_contract_world = transform_aabb_2d(pr005_local_min, pr005_local_max, pr005_origin_xy, pr005_yaw)

    # Aggregate actual validation-level mesh bounds.  The floor-zoning mesh is
    # reported separately from physical equipment.  Lights, cameras and post
    # process volumes are not treated as collision geometry.
    physical_meshes = [
        actor
        for actor in level_bounds
        if actor.get("class") == "StaticMeshActor"
        and actor.get("label", "").startswith("LB_PR005_")
        and "ValidationFloor" not in actor.get("label", "")
        and "FloorZoning" not in actor.get("label", "")
    ]
    zoned_meshes = [
        actor
        for actor in level_bounds
        if actor.get("class") == "StaticMeshActor"
        and actor.get("label", "").startswith("LB_PR005_")
        and "ValidationFloor" not in actor.get("label", "")
    ]

    def actor_union_local_xy(actors: list[dict[str, Any]]) -> dict[str, list[float]]:
        actor_aabbs = []
        for actor in actors:
            origin = actor["bounds_origin_cm"]
            extent = actor["bounds_extent_cm"]
            actor_aabbs.append(
                {
                    "min": [origin[0] - extent[0], origin[1] - extent[1]],
                    "max": [origin[0] + extent[0], origin[1] + extent[1]],
                    "size": [extent[0] * 2.0, extent[1] * 2.0],
                }
            )
        return union_aabbs(actor_aabbs)

    physical_local = actor_union_local_xy(physical_meshes)
    zoned_local = actor_union_local_xy(zoned_meshes)
    pr005_physical_world = transform_aabb_2d(
        physical_local["min"], physical_local["max"], pr005_origin_xy, pr005_yaw
    )
    pr005_zoned_world = transform_aabb_2d(
        zoned_local["min"], zoned_local["max"], pr005_origin_xy, pr005_yaw
    )

    input_port_world = integration["gameplay_ports_world_cm"]["PR005-IN-COIL"]
    boundary = current_boundary_x(PATHS["population_script"])
    fence_x = boundary["transfer_gate_x_cm"]

    # Positive values are clear gaps along material flow; negative values are
    # overlaps.  These are exact AABB values from the stated inputs.
    margins = {
        "pr003_target_to_pr004_centred_cm": rounded(pr004_envelope["min"][0] - pr003_target["max"][0]),
        "pr003_current_to_pr004_centred_cm": rounded(pr004_envelope["min"][0] - pr003_current["max"][0]),
        "pr004_centred_to_pr005_contract_cm": rounded(pr005_contract_world["min"][0] - pr004_envelope["max"][0]),
        "pr004_centred_to_pr005_actual_floor_zone_cm": rounded(pr005_zoned_world["min"][0] - pr004_envelope["max"][0]),
        "pr004_centred_to_pr005_actual_physical_mesh_cm": rounded(pr005_physical_world["min"][0] - pr004_envelope["max"][0]),
        "pr004_centred_east_edge_to_pr005_input_port_cm": rounded(float(input_port_world[0]) - pr004_envelope["max"][0]),
        "current_fence_to_pr005_contract_cm": rounded(pr005_contract_world["min"][0] - float(fence_x)) if fence_x is not None else None,
        "current_fence_to_pr005_actual_floor_zone_cm": rounded(pr005_zoned_world["min"][0] - float(fence_x)) if fence_x is not None else None,
        "pr004_centred_protrusion_past_current_fence_cm": rounded(pr004_envelope["max"][0] - float(fence_x)) if fence_x is not None else None,
    }

    # Determine whether the 1240 cm cell can fit between the target PR-003
    # occupied AABB and the conservative PR-005 contract while preserving the
    # explicit 120 cm audit assumption.  This does not move the station anchor;
    # it describes a possible local geometry offset for later design review.
    half_flow = pr004_size_xy[0] / 2.0
    feasible_center_min = pr003_target["max"][0] + ASSUMED_INTERSTATION_CLEARANCE_CM + half_flow
    feasible_center_max = pr005_contract_world["min"][0] - ASSUMED_INTERSTATION_CLEARANCE_CM - half_flow
    feasible = feasible_center_min <= feasible_center_max
    balanced_center = (feasible_center_min + feasible_center_max) / 2.0 if feasible else None
    balanced_shift = balanced_center - pr004_anchor_xy[0] if balanced_center is not None else None
    balanced_west = balanced_center - half_flow if balanced_center is not None else None
    balanced_east = balanced_center + half_flow if balanced_center is not None else None

    cradle_static = next(module for module in cradle_v001["modules"] if module["id"] == "static")
    cradle_local_xyz = [float(value) for value in cradle_static["local_bounds_xyz_cm"]]
    # Coil/cradle X axis must run across the canonical material-flow axis, so a
    # 90-degree plan rotation yields flow x = local y and across y = local x.
    cradle_world_xy = [cradle_local_xyz[1], cradle_local_xyz[0]]
    cradle_dimensional_fit = {
        "assumed_rotation": "local coil axis X rotated onto world Y; local Y becomes world material-flow X",
        "world_footprint_size_xy_cm": vector(cradle_world_xy),
        "remaining_cell_span_if_centred_xy_cm": vector(
            [pr004_size_xy[0] - cradle_world_xy[0], pr004_size_xy[1] - cradle_world_xy[1]]
        ),
        "fits_inside_outer_cell_envelope_by_dimensions_only": all(
            cradle_world_xy[index] <= pr004_size_xy[index] for index in range(2)
        ),
        "placement_validated": False,
        "reason": "The powered-cradle candidate has bounds, but its final PR-004 local transform and motion-swept bounds are not locked.",
    }

    contract_intersection = aabb_intersection_2d(pr004_envelope, pr005_contract_world)
    floor_intersection = aabb_intersection_2d(pr004_envelope, pr005_zoned_world)
    physical_intersection = aabb_intersection_2d(pr004_envelope, pr005_physical_world)

    unknowns = [
        "PR-004 robot candidate final local transform and complete J1-J6 motion-swept envelope",
        "PR-004 tool-changer and each docked/undocked tool swept envelope",
        "PR-004 surface-inspection gantry and bore-camera extension envelope",
        "PR-004 cabinet door, waste-bin lid and transfer/access-gate swept envelopes",
        "PR-004 crane/C-hook suspended-coil approach and withdrawal swept envelope",
        "PR-004 final component placement inside the proposed outer fence envelope",
        "authoritative inter-station clearance value (120 cm is an explicit audit assumption)",
    ]

    hard_failures = []
    if not all(anchor_checks.values()):
        hard_failures.append("authoritative_anchor_or_material_flow_consistency_failed")
    if contract_intersection["intersects"]:
        hard_failures.append("centred_pr004_outer_envelope_overlaps_pr005_gameplay_envelope")
    if floor_intersection["intersects"]:
        hard_failures.append("centred_pr004_outer_envelope_overlaps_pr005_actual_floor_zoning_mesh")
    if margins["pr004_centred_to_pr005_actual_physical_mesh_cm"] < ASSUMED_INTERSTATION_CLEARANCE_CM:
        hard_failures.append("centred_pr004_to_pr005_physical_mesh_clearance_below_120cm_audit_assumption")
    if fence_x is None or not boundary["consistent"]:
        hard_failures.append("current_pr004_pr005_fence_boundary_not_resolved")
    elif margins["pr004_centred_protrusion_past_current_fence_cm"] > 0.0:
        hard_failures.append("centred_pr004_outer_envelope_crosses_current_pr004_pr005_fence_boundary")
    if unknowns:
        hard_failures.append("required_motion_and_component_bounds_unknown")

    result = {
        "$schema": "line-boss/unreal/pr004-front-end-clearance-audit/v1",
        "status": "NOT_PASSED_REQUIRES_PR004_LOCAL_GEOMETRY_AND_FENCE_REBASE",
        "scope": "Read-only plan-view AABB audit; no anchors, runtime assets, maps or source candidates were changed.",
        "units": "centimetres unless otherwise stated",
        "material_flow": "+WORLD_X",
        "audit_assumptions": {
            "minimum_interstation_clearance_cm": ASSUMED_INTERSTATION_CLEARANCE_CM,
            "authority": "AUDIT_ASSUMPTION_NOT_DESIGN_LOCK",
            "reason": "The PR-004 contract contains 100-150 cm service/standoff requirements but no single authoritative adjacent-station clearance.",
            "aabb_rule": "Positive X margin is clear space; a negative margin is overlap.",
            "unknown_rule": "Any missing placement or motion-swept bound blocks a pass.",
        },
        "source_inputs": {name: source_record(path) for name, path in PATHS.items()},
        "anchor_and_flow_checks": anchor_checks,
        "anchors_preserved": {
            "PR-003_world_cm": vector(anchor_003["world_cm"]),
            "PR-004_world_cm": vector(anchor_004["world_cm"]),
            "PR-005_world_cm": vector(anchor_005["world_cm"]),
            "PR-005_yaw_degrees": rounded(pr005_yaw),
        },
        "pr003_store": {
            "population_map": population["map"],
            "slot_count": len(slots),
            "grid": {
                "flow_positions_x_cm": vector(distinct_flow_x),
                "across_positions_y_cm": vector(distinct_across_y),
                "shape": [len(distinct_flow_x), len(distinct_across_y)],
                "expected_shape": [3, 4],
                "shape_pass": [len(distinct_flow_x), len(distinct_across_y)] == [3, 4],
            },
            "current_populated_assets": {
                "coil": population["master_coil_asset"],
                "coil_world_footprint_xy_cm_after_yaw_90": vector(current_coil_world_xy),
                "saddle": current_saddle["asset"],
                "saddle_world_footprint_xy_cm": vector(current_saddle_xy),
                "occupied_union_world_xy_cm": bounds_record(pr003_current),
                "status": "CURRENT_GENERATED_MAP_CANDIDATES_NOT_PROMOTED",
            },
            "intended_replacement_candidates": {
                "coil": coil_v003["asset"],
                "coil_world_footprint_xy_cm_after_yaw_90": vector(target_coil_world_xy),
                "saddle": saddle_v002["asset"],
                "saddle_world_footprint_xy_cm": vector(target_saddle_xy),
                "occupied_union_world_xy_cm": bounds_record(pr003_target),
                "status": "SOURCE_CANDIDATES_NOT_IMPORTED_OR_PROMOTED",
            },
        },
        "pr004_cell": {
            "contract_status": pr004["status"],
            "centred_outer_envelope_world_xy_cm": bounds_record(pr004_envelope),
            "current_fence_boundary": boundary,
            "powered_cradle_candidate": cradle_dimensional_fit,
            "final_layout_proven": False,
        },
        "pr005_station": {
            "contract_envelope_world_xy_cm": bounds_record(pr005_contract_world),
            "actual_physical_mesh_union": {
                "actor_count": len(physical_meshes),
                "local_xy_cm": bounds_record(physical_local),
                "world_xy_cm_after_station_transform": bounds_record(pr005_physical_world),
            },
            "actual_mesh_union_including_floor_zoning": {
                "actor_count": len(zoned_meshes),
                "local_xy_cm": bounds_record(zoned_local),
                "world_xy_cm_after_station_transform": bounds_record(pr005_zoned_world),
            },
            "input_port_world_cm": vector(input_port_world),
            "orientation_pass": integration.get("material_flow_orientation_pass") is True,
        },
        "exact_material_flow_margins_cm": margins,
        "plan_intersections": {
            "pr004_centred_vs_pr005_contract": contract_intersection,
            "pr004_centred_vs_pr005_actual_floor_zone": floor_intersection,
            "pr004_centred_vs_pr005_actual_physical_mesh": physical_intersection,
        },
        "non_mutating_fit_option": {
            "purpose": "Demonstrate whether the anchors can remain fixed while future PR-004 child geometry is locally rebased; this audit does not apply the option.",
            "feasible_with_120cm_assumed_margin": feasible,
            "allowed_pr004_envelope_centre_x_range_cm": vector([feasible_center_min, feasible_center_max]),
            "allowed_local_x_offset_from_pr004_anchor_range_cm": vector(
                [feasible_center_min - pr004_anchor_xy[0], feasible_center_max - pr004_anchor_xy[0]]
            ),
            "balanced_envelope_centre_x_cm": rounded(balanced_center) if balanced_center is not None else None,
            "balanced_local_x_offset_from_anchor_cm": rounded(balanced_shift) if balanced_shift is not None else None,
            "balanced_envelope_flow_bounds_cm": vector([balanced_west, balanced_east]) if balanced_center is not None else None,
            "balanced_margin_to_pr003_target_cm": rounded(balanced_west - pr003_target["max"][0]) if balanced_center is not None else None,
            "balanced_margin_to_pr005_contract_cm": rounded(pr005_contract_world["min"][0] - balanced_east) if balanced_center is not None else None,
            "decision": "REQUIRES_EXPLICIT_LAYOUT_AND_FENCE_REVIEW; DO_NOT MOVE ANCHORS OR APPLY AUTOMATICALLY",
        },
        "unknown_or_unproven_bounds": unknowns,
        "hard_failures": hard_failures,
        "verdict": {
            "anchors_can_remain_preserved_for_next_design_iteration": feasible,
            "centred_pr004_contract_envelope_passes": False,
            "release_or_promotion_allowed": False,
            "required_next_action": "Rebase PR-004 child geometry approximately 210-232 cm west inside the unchanged PR-004 anchor frame, redesign the PR-004/PR-005 fence and transfer-gate line, then rerun with complete static and motion-swept component bounds.",
        },
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"PR004_FRONT_END_CLEARANCE_AUDIT_NOT_PASSED output={OUTPUT}")
    print(
        "margins_cm "
        f"PR003_to_PR004={margins['pr003_target_to_pr004_centred_cm']} "
        f"PR004_to_PR005_contract={margins['pr004_centred_to_pr005_contract_cm']} "
        f"PR004_to_PR005_physical={margins['pr004_centred_to_pr005_actual_physical_mesh_cm']}"
    )


if __name__ == "__main__":
    main()
