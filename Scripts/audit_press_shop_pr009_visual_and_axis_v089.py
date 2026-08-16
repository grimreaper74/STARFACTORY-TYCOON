#!/usr/bin/env python3
"""Record the authority correction and human-reviewed v089 release decision."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SCREENSHOTS = ROOT / "Saved/ValidationScreenshots/PressShopIntegration/v089_pr009_transfer_guide_collision"
PRO = ROOT / "SourceAssets/ReferencePacks/CAIRNWELL_PRESS_SHOP_REMAINING_MACHINERY_PACK_v1.0/visuals/SHEET_02_PR009_ENGINEERING_REFERENCE_4K.png"
SPEC = ROOT / "SourceAssets/ReferencePacks/CAIRNWELL_PRESS_SHOP_REMAINING_MACHINERY_PACK_v1.0/docs/PRESS_SHOP_REMAINING_MACHINERY_ENGINEERING_SPEC_v1.0.md"
SOURCE_REFERENCE = ROOT / "SourceAssets/PR009/AutomatedBlankStacker/Candidate_v002/PR009_Renders/v002/PR009_v002_isometric_restored.png"
AUDIT_DIR = ROOT / "Saved/Audits/PR009_InMap_v089"
OUT = ROOT / "Saved/Audits/press_shop_pr009_visual_review_v089.json"
AXIS_OUT = AUDIT_DIR / "axis_authority_correction.json"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def load(name):
    path = AUDIT_DIR / name
    return path, json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def main():
    expected = [
        SCREENSHOTS / f"press_shop_v089_pr009_transfer_guide_collision_{view}.png"
        for view in ("process", "interface", "cell", "elevated")
    ]
    failures = []
    screenshots = []
    for path in expected:
        if not path.is_file() or path.stat().st_size < 1024:
            failures.append(f"Missing or empty fixed-camera screenshot: {path.name}")
        else:
            screenshots.append({"file": str(path), "bytes": path.stat().st_size, "sha256": sha256(path)})
    evidence = {}
    for key, filename in (
        ("static", "release_collision_static_audit.json"),
        ("runtime", "runtime_pie_audit.json"),
        ("physical", "physical_collision_pie_audit.json"),
        ("navigation", "navigation_pie_audit.json"),
        ("sweeps", "collision_contract_sweep_audit.json"),
    ):
        path, payload = load(filename)
        evidence[key] = {"file": str(path), "sha256": sha256(path) if path.is_file() else None, "status": payload.get("status")}
        if not path.is_file() or not payload.get("status", "").startswith("PASS"):
            failures.append(f"Missing or failed technical evidence: {key}")

    axis = {
        "$schema": "cairnwell/audit/pr009-axis-authority-correction/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PRO_AXIS_AND_TOTAL_TRAVEL_INTERPRETATION_CORRECTED__V088_REJECTED__V087_RETAINED_AS_PARENT",
        "authoritative_sources": {
            "pro_sheet_02": {"file": str(PRO), "sha256": sha256(PRO)},
            "engineering_spec": {"file": str(SPEC), "sha256": sha256(SPEC)},
        },
        "coordinate_authority": {
            "station_local_x": "across strip/lane",
            "station_local_y": "material flow",
            "station_local_z": "up",
            "maximum_blank_mm_flow_by_across": [2600, 1800],
            "station_yaw_degrees": -90,
            "maximum_blank_world_half_extents_cm": [130, 90, 0.8],
        },
        "gantry_authority": {
            "module_03_source_centre_y_m": -0.3,
            "module_03_envelope_length_y_mm": 3100,
            "m02_total_travel_mm": 2800,
            "correct_endpoint_offsets_from_source_midpoint_m": [-1.4, 1.4],
            "incorrect_rejected_interpretation": "0 to +2.8 m displacement from the authored midpoint",
        },
        "consequence": {
            "original_v087_trace_portal_clearance": "PASS under corrected authoritative axes/range",
            "experimental_v088": "REJECTED_NOT_PROMOTED; dimensionally valid derived source but runtime/design necessity disproved",
            "actual_remaining_collision_issue": "Combined transfer-guide auto collision filled its open channel; corrected with two authored side boxes in v089",
        },
        "v087_map_modified": False,
        "v088_promoted": False,
        "promotion_authorized": False,
    }
    AXIS_OUT.parent.mkdir(parents=True, exist_ok=True)
    AXIS_OUT.write_text(json.dumps(axis, indent=2) + "\n", encoding="utf-8")

    collision_ready = not failures
    payload = {
        "$schema": "line-boss/audit/press-shop-pr009-visual-v089/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": (
            "FRESH_FIXED_CAMERA_UNREAL_EVIDENCE_COMPLETE__RELEASE_COLLISION_RUNTIME_SAVE_AUTHORITY_AND_NAVIGATION_PASS__"
            "VISUAL_TYPOGRAPHY_SERVICE_SIDE_CAMERA_ENVIRONMENT_AND_PRESENTATION_HOLD__RETAINED__NOT_PROMOTED"
            if not failures else "PR009_V089_EVIDENCE_INCOMPLETE__NOT_PROMOTED"
        ),
        "map": "/Game/LineBoss/Maps/LB_PressShop_PR009TransferGuideCollisionCandidate_v089",
        "references": {
            "authoritative_pro_sheet_02": {"file": str(PRO), "sha256": sha256(PRO)},
            "corrected_v002_source_isometric": {"file": str(SOURCE_REFERENCE), "sha256": sha256(SOURCE_REFERENCE)},
            "axis_authority_correction": {"file": str(AXIS_OUT), "sha256": sha256(AXIS_OUT)},
        },
        "screenshots": screenshots,
        "human_review": {
            "passes": [
                "The authored two-box transfer-guide collision is invisible and preserves v087/v086 visual geometry, materials and camera composition.",
                "Open-mesh guarding, blank steel, amber light curtains, roller paths and the calibrated Cairnwell green/charcoal/yellow hierarchy remain readable.",
                "The maximum 2600 mm flow x 1800 mm across blank now traverses the interface without hitting either physical guide rail.",
            ],
            "visual_release_holds": [
                "Cairnwell Automotive / Moorcross Works identity remains too small and soft at fixed management-camera distance.",
                "The current four cameras still miss the south service face containing the authored HMI and electrical cabinet.",
                "The hall and floor are too clean, bright and sparse compared with Pro Sheet 02's installed industrial context.",
                "The interface and elevated views remain technical validation compositions rather than final control-room CCTV presentation.",
                "The cell still needs stronger enclosure depth and supported service/mechanical density after existing modules are shown from the correct side.",
            ],
            "decision": "Retain v089 as the technically release-collision-ready parent, but do not promote PR-009. Next add an early-gated south-west service/hero fixed camera and improve CCTV identity/installed presentation without changing accepted collision or process geometry.",
        },
        "technical_evidence": evidence,
        "release_collision_ready": collision_ready,
        "visual_release_ready": False,
        "promotion_authorized": False,
        "pr010_started": False,
        "robots_modified": False,
        "failures": failures,
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": payload["status"], "release_collision_ready": collision_ready, "visual_release_ready": False, "failures": failures}, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
