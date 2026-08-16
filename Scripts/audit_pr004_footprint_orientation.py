"""Compare the two possible PR-004 cell footprint orientations.

This is a read-only plan-level audit.  It does not move station anchors, edit
the Unreal level, import source candidates, or claim complete swept clearance.
The detailed PR-004-DS-001 sheet is NTS and explicitly defers master-plan
position authority to the Press Shop master plan, so both interpretations are
tested against the fixed PR-003 and PR-005 anchors.
"""

from __future__ import annotations

import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
INPUT = REPO / "Saved" / "Audits" / "pr004_pr005_clearance_v001.json"
OUTPUT = REPO / "Saved" / "Audits" / "pr004_footprint_orientation_v001.json"
ASSUMED_MARGIN_CM = 120.0


def rounded(value: float) -> float:
    return round(float(value), 3)


def scenario(
    name: str,
    flow_length_cm: float,
    across_width_cm: float,
    anchor_x_cm: float,
    pr003_max_x_cm: float,
    pr005_contract_min_x_cm: float,
    pr005_floor_min_x_cm: float,
    pr005_physical_min_x_cm: float,
    current_fence_x_cm: float,
) -> dict:
    half = flow_length_cm / 2.0
    centred_min = anchor_x_cm - half
    centred_max = anchor_x_cm + half
    raw_corridor = pr005_contract_min_x_cm - pr003_max_x_cm
    usable_corridor = raw_corridor - 2.0 * ASSUMED_MARGIN_CM

    allowed_min = pr003_max_x_cm + ASSUMED_MARGIN_CM + half
    allowed_max = pr005_contract_min_x_cm - ASSUMED_MARGIN_CM - half
    feasible_with_margin = allowed_min <= allowed_max

    raw_allowed_min = pr003_max_x_cm + half
    raw_allowed_max = pr005_contract_min_x_cm - half
    feasible_without_margin = raw_allowed_min <= raw_allowed_max
    raw_balanced_center = (raw_allowed_min + raw_allowed_max) / 2.0 if feasible_without_margin else None
    raw_balanced_edge_min = raw_balanced_center - half if raw_balanced_center is not None else None
    raw_balanced_edge_max = raw_balanced_center + half if raw_balanced_center is not None else None

    return {
        "name": name,
        "flow_length_cm": rounded(flow_length_cm),
        "across_width_cm": rounded(across_width_cm),
        "centred_world_flow_bounds_cm": [rounded(centred_min), rounded(centred_max)],
        "centred_margins_cm": {
            "from_pr003_target_occupied": rounded(centred_min - pr003_max_x_cm),
            "to_pr005_contract": rounded(pr005_contract_min_x_cm - centred_max),
            "to_pr005_floor_zone": rounded(pr005_floor_min_x_cm - centred_max),
            "to_pr005_physical_mesh": rounded(pr005_physical_min_x_cm - centred_max),
            "protrusion_past_current_fence": rounded(centred_max - current_fence_x_cm),
        },
        "corridor_cm": {
            "raw_between_pr003_and_pr005_contract": rounded(raw_corridor),
            "usable_after_two_120cm_audit_margins": rounded(usable_corridor),
            "flow_length_surplus_or_deficit_with_margins": rounded(usable_corridor - flow_length_cm),
        },
        "fit_with_120cm_audit_margin": {
            "feasible": feasible_with_margin,
            "allowed_envelope_centre_x_range_cm": [rounded(allowed_min), rounded(allowed_max)],
            "allowed_local_x_offset_from_anchor_range_cm": [
                rounded(allowed_min - anchor_x_cm),
                rounded(allowed_max - anchor_x_cm),
            ],
        },
        "raw_non_overlap_fit_without_service_margin": {
            "feasible": feasible_without_margin,
            "allowed_envelope_centre_x_range_cm": [rounded(raw_allowed_min), rounded(raw_allowed_max)],
            "balanced_centre_x_cm": rounded(raw_balanced_center) if raw_balanced_center is not None else None,
            "balanced_edge_bounds_cm": [rounded(raw_balanced_edge_min), rounded(raw_balanced_edge_max)] if raw_balanced_center is not None else None,
            "balanced_margins_to_pr003_and_pr005_cm": [
                rounded(raw_balanced_edge_min - pr003_max_x_cm),
                rounded(pr005_contract_min_x_cm - raw_balanced_edge_max),
            ] if raw_balanced_center is not None else None,
        },
    }


def main() -> None:
    base = json.loads(INPUT.read_text(encoding="utf-8-sig"))
    anchor_x = float(base["anchors_preserved"]["PR-004_world_cm"][0])
    pr003_max_x = float(base["pr003_store"]["intended_replacement_candidates"]["occupied_union_world_xy_cm"]["max"][0])
    pr005_contract_min_x = float(base["pr005_station"]["contract_envelope_world_xy_cm"]["min"][0])
    pr005_floor_min_x = float(base["pr005_station"]["actual_mesh_union_including_floor_zoning"]["world_xy_cm_after_station_transform"]["min"][0])
    pr005_physical_min_x = float(base["pr005_station"]["actual_physical_mesh_union"]["world_xy_cm_after_station_transform"]["min"][0])
    fence_x = float(base["pr004_cell"]["current_fence_boundary"]["transfer_gate_x_cm"])

    normalized = scenario(
        "MASTER_PLAN_NORMALIZED_12_4M_FLOW_14_4M_ACROSS",
        1240.0,
        1440.0,
        anchor_x,
        pr003_max_x,
        pr005_contract_min_x,
        pr005_floor_min_x,
        pr005_physical_min_x,
        fence_x,
    )
    literal = scenario(
        "LITERAL_SHEET_HORIZONTAL_14_4M_FLOW_12_4M_ACROSS",
        1440.0,
        1240.0,
        anchor_x,
        pr003_max_x,
        pr005_contract_min_x,
        pr005_floor_min_x,
        pr005_physical_min_x,
        fence_x,
    )

    result = {
        "$schema": "line-boss/unreal/pr004-footprint-orientation-audit/v1",
        "status": "LOCK_1240CM_FLOW_1440CM_ACROSS_PENDING_COMPLETE_SWEPT_BOUNDS",
        "scope": "Read-only plan AABB comparison; no anchors, levels, runtime assets or source candidates changed.",
        "units": "centimetres",
        "material_flow": "+WORLD_X",
        "authority": {
            "master_plan_position": "Content/LineBoss/Data/press_shop_master_plan_anchors_v001.json",
            "prior_clearance_audit": "Saved/Audits/pr004_pr005_clearance_v001.json",
            "whole_cell_sheet": "Docs/References/PR004_Robotic_Depackaging_Cell/v002/PR004A_Realistic_Robotic_Coil_Destrapping_Dewrapping_Cell_v002.jpg",
            "detailed_module_sheet": "Docs/References/PR004_Robotic_Depackaging_Cell/v002/PR004_Powered_Coil_Wrap_Dewinding_Compaction_Module_RevA.jpg",
            "sheet_note": "PR-004-DS-001 is NTS and says master-plan position is authoritative; pixel measurement is forbidden.",
        },
        "fixed_inputs": {
            "pr004_anchor_x_cm": rounded(anchor_x),
            "pr003_target_occupied_max_x_cm": rounded(pr003_max_x),
            "pr005_contract_min_x_cm": rounded(pr005_contract_min_x),
            "pr005_floor_zone_min_x_cm": rounded(pr005_floor_min_x),
            "pr005_physical_mesh_min_x_cm": rounded(pr005_physical_min_x),
            "current_pr004_pr005_fence_x_cm": rounded(fence_x),
            "audit_interstation_margin_cm": ASSUMED_MARGIN_CM,
            "audit_margin_status": "EXPLICIT_ASSUMPTION_NOT_A_FABRICATION_DIMENSION",
        },
        "scenarios": [normalized, literal],
        "decision": {
            "selected": normalized["name"],
            "reason": "The 1240 cm flow orientation can fit between the fixed PR-003 and PR-005 contract envelopes with two 120 cm audit margins only after a controlled PR-004 child-geometry rebase. The 1440 cm flow interpretation is 178 cm too long for those margins, and centred it overlaps the PR-005 contract by 190 cm, its floor zone by 128.25 cm and its physical mesh by 27 cm.",
            "literal_1440cm_flow_rejected_for_placement": True,
            "process_topology_retained": "Keep the sheet's coil-arrival, robot tab handoff, spindle, dancer, compactor and PR-005 handoff sequence, but normalize the internal arrangement to the master-plan coordinate system.",
            "anchors_moved": False,
            "level_changed": False,
            "import_allowed": False,
        },
        "remaining_blockers": [
            "Apply no local rebase until complete cradle, robot, tool, spindle, guard, gate, cabinet, bin and crane swept bounds are assembled.",
            "Redesign and validate the PR-004/PR-005 fence and transfer-gate boundary after the child-geometry rebase is selected.",
            "The 120 cm interstation margin remains an audit assumption and must be reconciled with final maintenance access routes.",
        ],
        "promotion": "FORBIDDEN; this audit selects an orientation but does not prove final layout clearance or runtime quality.",
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(result["status"])
    print(f"output={OUTPUT}")
    print(
        "literal_14_4m_flow "
        f"margin_deficit_cm={literal['corridor_cm']['flow_length_surplus_or_deficit_with_margins']} "
        f"centred_to_pr005_physical_cm={literal['centred_margins_cm']['to_pr005_physical_mesh']}"
    )


if __name__ == "__main__":
    main()
