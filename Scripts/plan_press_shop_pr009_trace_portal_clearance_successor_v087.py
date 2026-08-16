#!/usr/bin/env python3
"""Plan a trace-portal relocation that preserves PR-009's authoritative 2.8 m gantry contract."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SWEEP = ROOT / "Saved/Audits/PR009_InMap_v087/collision_contract_sweep_audit.json"
SOURCE = ROOT / "Saved/Audits/PR009_InMap_v087/source_collision_evidence.json"
BOUNDS = ROOT / "Saved/Audits/press_shop_pr009_presentation_bounds_v085.json"
OUT = ROOT / "Saved/Audits/PR009_InMap_v087/trace_portal_clearance_successor_plan.json"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main():
    required = (SWEEP, SOURCE, BOUNDS)
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError(f"Missing authoritative evidence: {missing}")
    sweep = json.loads(SWEEP.read_text(encoding="utf-8"))
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    bounds = json.loads(BOUNDS.read_text(encoding="utf-8"))

    linear = {row["object"]: row for row in sweep["linear_contract_sweeps"]}
    bridge = linear["PR009_M02_GantryBridge_01"]
    cross = linear["PR009_M03_GantryCrossSlide_01"]
    z_axis = linear["PR009_M04_GantryZ_Carriage_01"]
    moving_y_max = max(row["swept_max_m"][1] for row in (bridge, cross, z_axis))

    trace_rows = source["static_groups"]["SM_CA_MW_PR009_TracePortal_01"]
    trace_min_y = min(row["bounds_min_m"][1] for row in trace_rows)
    trace_max_y = max(row["bounds_max_m"][1] for row in trace_rows)
    trace_center_y = (trace_min_y + trace_max_y) * 0.5
    trace_half_y = (trace_max_y - trace_min_y) * 0.5

    posts = {row["name"]: row for row in trace_rows if row["semantic"] == "trace_portal_post"}
    left_post = posts["PR009_07_TracePost_L"]
    right_post = posts["PR009_07_TracePost_R"]
    current_clear_opening_x = right_post["bounds_min_m"][0] - left_post["bounds_max_m"][0]
    pro_max_blank_width_x = 2.60
    target_clear_opening_x = 2.80
    portal_width_scale_x = target_clear_opening_x / current_clear_opening_x
    blank_side_clearance_m = (target_clear_opening_x - pro_max_blank_width_x) * 0.5

    # Place the scanner over the output conveyor while retaining useful clearance
    # from the cross-slide's authoritative full-contract envelope.
    proposed_center_y = 3.15
    proposed_min_y = proposed_center_y - trace_half_y
    proposed_max_y = proposed_center_y + trace_half_y
    mover_clearance_m = proposed_min_y - moving_y_max
    cell_max_y = sweep["guarded_cell_source_envelope"]["y_m"][1]
    guard_clearance_m = cell_max_y - proposed_max_y

    trace_bound = next(
        row for row in bounds["records"] if row["actor"].endswith("SM_CA_MW_PR009_TracePortal_01"))
    current_world_x = trace_bound["origin_cm"][0]
    source_delta_y_m = proposed_center_y - trace_center_y
    # Source +Y maps to decreasing world X in the verified station basis.
    proposed_world_x = current_world_x - source_delta_y_m * 100.0

    if mover_clearance_m < 0.15:
        raise RuntimeError(f"Proposed portal/mover clearance is too small: {mover_clearance_m} m")
    if guard_clearance_m < 0.40:
        raise RuntimeError(f"Proposed portal/guard clearance is too small: {guard_clearance_m} m")

    payload = {
        "$schema": "cairnwell/plan/press-shop-pr009-trace-portal-clearance-successor-v087/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PR009_V087_TRACE_PORTAL_CLEARANCE_SUCCESSOR_PLAN_PASS__UNREAL_REBUILD_AND_ALL_GATES_REQUIRED__NOT_PROMOTED",
        "decision": (
            "Preserve the authoritative 2800 mm gantry bridge travel. In the next isolated successor, move the complete trace-portal "
            "visual and its authored collision together toward the output conveyor and widen its clear opening from 2600 to 2800 mm; "
            "do not reduce the motion contract and do not edit v087."
        ),
        "current_source_portal_envelope_m": {
            "min_y": trace_min_y,
            "max_y": trace_max_y,
            "centre_y": trace_center_y,
            "half_width_y": trace_half_y,
        },
        "authoritative_mover_envelopes_m": {
            "bridge_max_y": bridge["swept_max_m"][1],
            "cross_slide_max_y": cross["swept_max_m"][1],
            "z_carriage_max_y": z_axis["swept_max_m"][1],
            "governing_max_y": moving_y_max,
            "bridge_contract_mm": bridge["source_contract"]["range_mm"],
        },
        "proposed_portal_envelope_m": {
            "centre_y": proposed_center_y,
            "min_y": proposed_min_y,
            "max_y": proposed_max_y,
            "clearance_to_governing_mover_m": mover_clearance_m,
            "clearance_to_guarded_cell_end_m": guard_clearance_m,
            "current_clear_opening_x": current_clear_opening_x,
            "target_clear_opening_x": target_clear_opening_x,
            "pro_max_blank_width_x": pro_max_blank_width_x,
            "blank_side_clearance_m": blank_side_clearance_m,
        },
        "unreal_actor_transform_cm": {
            "actor_match_suffix": "SM_CA_MW_PR009_TracePortal_01",
            "current_world_x": current_world_x,
            "proposed_world_x": proposed_world_x,
            "world_x_delta": proposed_world_x - current_world_x,
            "world_y_and_z": "unchanged",
            "required_local_x_width_factor": portal_width_scale_x,
            "release_asset_policy": (
                "Author and import a dimensioned derived trace-portal mesh with the widened opening; do not leave non-identity actor scale "
                "as the final release asset. Preserve the immutable v002 source and store the derived Blender/FBX/manifest separately."
            ),
            "visual_and_collision_move_together": True,
        },
        "required_successor_proofs": [
            "Fresh measured actor bounds after relocation",
            "Zero unapproved full-contract mover-vs-blocking-primitive overlaps",
            "Full 1800 x 2600 mm blank sweep through infeed, vision, stack and output corridor",
            "Portal posts remain outside the blank and carrier path; output rollers retain lateral clearance",
            "Imported replacement trace-portal component scale is identity after the dimensioned width change is baked into the derived source asset",
            "All current PIE motion, save, authority, transactional handoff and navigation gates remain green",
            "Fresh fixed-camera Unreal screenshots prove the portal still reads as a traceability station",
            "Human visual comparison against Pro Sheet 02 and the corrected v002 source render",
        ],
        "evidence": {str(path): sha256(path) for path in required},
        "v087_modified": False,
        "promotion_authorized": False,
        "pr010_started": False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": payload["status"], "output": str(OUT)}, indent=2))


if __name__ == "__main__":
    main()
