#!/usr/bin/env python3
"""Record the human-reviewed PR-009 v086 decision against Pro Sheet 02 and v002 source."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SCREENSHOTS = ROOT / "Saved/ValidationScreenshots/PressShopIntegration/v086_pr009_layered"
REFERENCE = ROOT / (
    "SourceAssets/ReferencePacks/CAIRNWELL_PRESS_SHOP_REMAINING_MACHINERY_PACK_v1.0/"
    "visuals/SHEET_02_PR009_ENGINEERING_REFERENCE_4K.png")
SOURCE_REFERENCE = Path(
    r"C:\Users\greg_\Projects\LineBoss_PR009_PR010_Staging\PR009_Renders\v002"
    r"\PR009_v002_isometric_restored.png")
TECHNICAL = ROOT / "Saved/Audits/PR009_InMap_v086/PR009_IN_MAP_TECHNICAL_VERIFICATION.json"
OUT = ROOT / "Saved/Audits/press_shop_pr009_visual_review_v086.json"
EXPECTED = tuple(
    f"press_shop_v086_pr009_layered_{name}.png" for name in ("process", "interface", "cell", "elevated"))


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main():
    failures = []
    screenshots = []
    for name in EXPECTED:
        path = SCREENSHOTS / name
        if not path.is_file() or path.stat().st_size < 1024:
            failures.append(f"Missing or empty fixed-camera screenshot: {name}")
        else:
            screenshots.append({"file": str(path), "bytes": path.stat().st_size, "sha256": sha256(path)})
    for label, path in (
        ("Pro Sheet 02", REFERENCE),
        ("corrected v002 source render", SOURCE_REFERENCE),
        ("v086 technical verification", TECHNICAL),
    ):
        if not path.is_file():
            failures.append(f"Missing {label}")

    technical_status = None
    release_collision_ready = False
    if TECHNICAL.is_file():
        technical = json.loads(TECHNICAL.read_text(encoding="utf-8"))
        technical_status = technical.get("status")
        release_collision_ready = any(
            gate.get("id") == "G6_COLLISION_COVERAGE_AND_PROFILE_EVIDENCE"
            and gate.get("release_collision_ready") is True
            for gate in technical.get("gates", []))

    status = (
        "FRESH_FIXED_CAMERA_UNREAL_EVIDENCE_COMPLETE__DARKER_CALIBRATION_NEAR_GUARD_IDENTITY_BLANK_STEEL_AND_LIGHT_CURTAIN_DIRECTION_PASS__"
        "TYPOGRAPHY_MECHANICAL_DENSITY_ENVIRONMENT_AND_RELEASE_COLLISION_HOLD__RETAINED__NOT_PROMOTED"
        if not failures else "PR009_V086_VISUAL_EVIDENCE_INCOMPLETE__NOT_PROMOTED")
    result = {
        "$schema": "line-boss/audit/press-shop-pr009-visual-v086/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "map": "/Game/LineBoss/Maps/LB_PressShop_PR009LayeredPresentationCandidate_v086",
        "references": {
            "authoritative_pro_sheet_02": {
                "file": str(REFERENCE),
                "sha256": sha256(REFERENCE) if REFERENCE.is_file() else None,
            },
            "corrected_source_isometric": {
                "file": str(SOURCE_REFERENCE),
                "sha256": sha256(SOURCE_REFERENCE) if SOURCE_REFERENCE.is_file() else None,
            },
        },
        "screenshots": screenshots,
        "human_review": {
            "improvements_over_v085": [
                "The darker calibration gives the guarded cell, gantry and blank stack more depth than v085.",
                "The Cairnwell Automotive / Moorcross Works identity plate is now on the measured near guard face and appears in the fixed views.",
                "Safety yellow is less overpowering, while blank steel, machined rollers and structural members remain distinguishable.",
                "The amber light curtains remain visible and the process path is readable from process and cell views.",
            ],
            "remaining_fails": [
                "The near-guard identity typography is too small and soft at the intended camera distances.",
                "The installed cell still lacks the dense service hardware, cabinets, hoses, sensors and mechanical mass visible in Pro Sheet 02.",
                "The surrounding hall and floor remain too clean, bright and sparse to provide the reference's grounded industrial presentation.",
                "The interface camera is technically useful but not yet a release-quality management-game composition.",
                "The elevated view still reads as a modular assembly/blockout presentation rather than a finished installed machine.",
                "The technical verification explicitly reports temporary complex-as-simple collision and release_collision_ready=false.",
            ],
            "decision": (
                "Retain v086 as the current calibrated visual and technical baseline. Do not promote. "
                "Create an isolated successor with authored release collision and continue presentation refinement; "
                "repeat the complete technical suite and fresh fixed-camera visual review before promotion."
            ),
        },
        "technical_verification": {
            "file": str(TECHNICAL),
            "sha256": sha256(TECHNICAL) if TECHNICAL.is_file() else None,
            "status": technical_status,
            "release_collision_ready": release_collision_ready,
        },
        "promotion_authorized": False,
        "pr010_started": False,
        "failures": failures,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": status,
        "technical_status": technical_status,
        "release_collision_ready": release_collision_ready,
        "failures": failures,
    }, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
