#!/usr/bin/env python3
"""Record the human-reviewed PR-009 v084 fixed-camera decision against Pro Sheet 02."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SCREENSHOTS = ROOT / "Saved/ValidationScreenshots/PressShopIntegration/v084_pr009_corrected"
REFERENCE = ROOT / (
    "SourceAssets/ReferencePacks/CAIRNWELL_PRESS_SHOP_REMAINING_MACHINERY_PACK_v1.0/"
    "visuals/SHEET_02_PR009_ENGINEERING_REFERENCE_4K.png"
)
SOURCE_REFERENCE = Path(
    r"C:\Users\greg_\Projects\LineBoss_PR009_PR010_Staging\PR009_Renders\v002"
    r"\PR009_v002_isometric_restored.png"
)
OUT = ROOT / "Saved/Audits/press_shop_pr009_visual_review_v084.json"
EXPECTED = (
    "press_shop_v084_pr009_corrected_process.png",
    "press_shop_v084_pr009_corrected_interface.png",
    "press_shop_v084_pr009_corrected_cell.png",
    "press_shop_v084_pr009_corrected_elevated.png",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main() -> int:
    failures = []
    evidence = []
    for name in EXPECTED:
        path = SCREENSHOTS / name
        if not path.is_file() or path.stat().st_size < 1024:
            failures.append(f"Missing or empty fixed-camera screenshot: {name}")
            continue
        evidence.append({"file": str(path), "bytes": path.stat().st_size, "sha256": sha256(path)})
    if not REFERENCE.is_file():
        failures.append("Missing authoritative Pro Sheet 02 PR-009 reference")
    if not SOURCE_REFERENCE.is_file():
        failures.append("Missing corrected PR-009 v002 source-render reference")

    result = {
        "$schema": "line-boss/audit/press-shop-pr009-visual-v084/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": (
            "FRESH_FIXED_CAMERA_UNREAL_EVIDENCE_COMPLETE__CORRECTED_MODULAR_GEOMETRY_DIRECTION_PASS__"
            "PRO_SHEET_02_MATERIAL_LIGHTING_IDENTITY_AND_PRESENTATION_GATE_FAIL__NOT_PROMOTED"
            if not failures else "PR009_V084_VISUAL_EVIDENCE_INCOMPLETE__NOT_PROMOTED"
        ),
        "map": "/Game/LineBoss/Maps/LB_PressShop_PR009CorrectedIntegrationCandidate_v084",
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
        "screenshots": evidence,
        "human_review": {
            "passes": [
                "The corrected semantic modular import reconstructs a coherent guarded PR-009 cell at the fixed datum.",
                "The PR-008 to PR-009 supported roller-transfer span reads continuously and the process direction is understandable.",
                "Open-mesh guarding, gantry rails, roller beds, lift/stack zone and service-side cabinets are present.",
                "No in-world Line Boss branding is visible in the reviewed frames.",
            ],
            "fails": [
                "The bright, largely uniform materials read as clean blockout plastic rather than layered industrial finishes.",
                "The blank stack and several mechanisms collapse into near-black masses instead of reading as exposed or oiled sheet steel.",
                "Safety yellow is over-dominant and too uniformly saturated, weakening machine hierarchy and scale.",
                "Gantry, cabinets, rollers, guarding and floor lack the controlled roughness, wear, fastener and service-detail contrast shown by Pro Sheet 02 and the corrected source render.",
                "Light curtains, HMI/screen state and Cairnwell/Moorcross station identity are missing, weak or illegible at the fixed management cameras.",
                "White hall floor/wall/column response is clipped and flat, preventing believable installed-factory depth.",
                "The fixed cameras prove geometry but do not yet provide release-quality CCTV composition or tonal separation.",
            ],
            "decision": (
                "Reject v084 for promotion. Retain it only as the corrected modular/native-binding technical baseline; "
                "build isolated v085 with explicit material-role mapping, visible worked-sheet steel, restrained safety colour, "
                "emissive HMI/light curtains, readable identity and calibrated industrial lighting before repeating every gate."
            ),
        },
        "promotion_authorized": False,
        "pr010_started": False,
        "failures": failures,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "failures": failures}, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
