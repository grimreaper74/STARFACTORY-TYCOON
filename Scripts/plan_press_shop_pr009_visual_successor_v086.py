#!/usr/bin/env python3
"""Create the evidence-backed visual-successor brief for retained PR-009 v086."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
BOUNDS = ROOT / "Saved/Audits/press_shop_pr009_presentation_bounds_v085.json"
VISUAL = ROOT / "Saved/Audits/press_shop_pr009_visual_review_v086.json"
TECHNICAL = ROOT / "Saved/Audits/PR009_InMap_v086/PR009_IN_MAP_TECHNICAL_VERIFICATION.json"
OUT = ROOT / "Saved/Audits/press_shop_pr009_visual_successor_plan_v086.json"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main():
    required = (BOUNDS, VISUAL, TECHNICAL)
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError(f"Missing authoritative evidence: {missing}")

    bounds_payload = json.loads(BOUNDS.read_text(encoding="utf-8"))
    records = {record["actor"].split("_V085_")[-1]: record for record in bounds_payload["records"]}
    required_records = (
        "SM_CA_MW_PR009_GuardSet_01",
        "SM_CA_MW_PR009_HMI_01",
        "SM_CA_MW_PR009_ElectricalCabinet_01",
        "SM_CA_MW_PR009_TracePortal_01",
    )
    absent_records = [name for name in required_records if name not in records]
    if absent_records:
        raise RuntimeError(f"Missing measured PR-009 records: {absent_records}")

    guard = records["SM_CA_MW_PR009_GuardSet_01"]
    hmi = records["SM_CA_MW_PR009_HMI_01"]
    cabinet = records["SM_CA_MW_PR009_ElectricalCabinet_01"]
    portal = records["SM_CA_MW_PR009_TracePortal_01"]
    payload = {
        "$schema": "cairnwell/plan/press-shop-pr009-visual-successor-v086/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PR009_V086_EVIDENCE_BACKED_VISUAL_SUCCESSOR_PLAN_COMPLETE__NO_UNREAL_ASSETS_MODIFIED__NOT_PROMOTED",
        "parent_policy": {
            "current_retained_map": "/Game/LineBoss/Maps/LB_PressShop_PR009LayeredPresentationCandidate_v086",
            "successor_parent": "Use the isolated collision-successor map only after its evidence is independently accepted; never modify v086 in place.",
            "promotion_authorized": False,
        },
        "measured_service_side": {
            "guard_near_y_cm": guard["max_cm"][1],
            "guard_far_y_cm": guard["min_cm"][1],
            "hmi_origin_cm": hmi["origin_cm"],
            "hmi_bounds_cm": {"min": hmi["min_cm"], "max": hmi["max_cm"]},
            "electrical_cabinet_origin_cm": cabinet["origin_cm"],
            "trace_portal_origin_cm": portal["origin_cm"],
            "finding": (
                "All v086 validation cameras are north/near-side of the cell, while the authored HMI and electrical cabinet sit on the "
                "south/far service face around Y -2240.5 and -2208 cm. Their weak visibility is therefore primarily a camera/side-selection problem, "
                "not evidence that those source modules are absent."
            ),
        },
        "next_visual_actions_in_order": [
            {
                "priority": 1,
                "action": "Add one fixed south-west service/hero camera before inventing geometry.",
                "trial_transform_cm": {"location": [0.0, -2820.0, 400.0], "target": [550.0, -2020.0, 130.0], "fov_degrees": 50.0},
                "must_show": ["authored HMI", "electrical cabinet", "trace portal", "gantry", "blank stack", "open-mesh guarding"],
                "gate": "Early single-camera Unreal capture compared with the corrected v002 hero; reject if HMI/cabinet remain hidden or the process silhouette regresses.",
            },
            {
                "priority": 2,
                "action": "Increase diegetic identity hierarchy using measured guard faces.",
                "requirements": [
                    "Retain Cairnwell Automotive and Moorcross Works only; never use Line Boss in-world.",
                    "Use a larger mounted plate and text sized for the fixed CCTV distance, with a service-side duplicate only if the new camera proves it useful.",
                    "Do not cover open mesh, gates, light curtains, HMI access or maintenance clearance.",
                ],
            },
            {
                "priority": 3,
                "action": "Improve installed-machine grounding without changing station datums or hall structure.",
                "requirements": [
                    "Prefer authored base plinths/feet, supported local cable or service drops and restrained machine-island floor treatment.",
                    "Do not hide the real hall column or add floating walls, unsupported service lines or presentation-only collision.",
                    "Keep additions navigation-neutral unless they represent a real physical envelope.",
                ],
            },
            {
                "priority": 4,
                "action": "Only then add missing close-inspection service detail proven absent from existing meshes.",
                "requirements": [
                    "Audit the existing 158 semantic modular actors and ten static groups first; hoses, energy chain, sensors, HMI, cabinet and trace portal already exist.",
                    "Add no decorative bolts/cables solely to raise actor count.",
                    "Preserve all native mover attachments and release collision envelopes.",
                ],
            },
        ],
        "mandatory_successor_gates": [
            "UE 5.8 compile/import",
            "PR-008/PR-009 transactional traceability",
            "all PR-009 presentation motion in PIE",
            "safe save/load and trusted remote authority/isolation/zero-energy",
            "release simple/convex/UCX collision with nonblocking mover paths",
            "protected navigation",
            "fresh fixed-camera screenshots including the service/hero view",
            "human comparison with Pro Sheet 02 and corrected v002 source render",
        ],
        "evidence": {str(path): sha256(path) for path in required},
        "unreal_assets_modified": False,
        "pr010_started": False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": payload["status"], "output": str(OUT)}, indent=2))


if __name__ == "__main__":
    main()
