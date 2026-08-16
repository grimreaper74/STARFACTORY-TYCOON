#!/usr/bin/env python3
"""Record the human-reviewed PR-009 v085 decision against Pro Sheet 02 and v002 source."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SCREENSHOTS = ROOT / "Saved/ValidationScreenshots/PressShopIntegration/v085_pr009_layered"
REFERENCE = ROOT / (
    "SourceAssets/ReferencePacks/CAIRNWELL_PRESS_SHOP_REMAINING_MACHINERY_PACK_v1.0/"
    "visuals/SHEET_02_PR009_ENGINEERING_REFERENCE_4K.png")
SOURCE_REFERENCE = Path(
    r"C:\Users\greg_\Projects\LineBoss_PR009_PR010_Staging\PR009_Renders\v002"
    r"\PR009_v002_isometric_restored.png")
OUT = ROOT / "Saved/Audits/press_shop_pr009_visual_review_v085.json"
EXPECTED = tuple(
    f"press_shop_v085_pr009_layered_{name}.png" for name in ("process", "interface", "cell", "elevated"))


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
    for label, path in (("Pro Sheet 02", REFERENCE), ("corrected v002 source render", SOURCE_REFERENCE)):
        if not path.is_file():
            failures.append(f"Missing {label}")
    status = (
        "FRESH_FIXED_CAMERA_UNREAL_EVIDENCE_COMPLETE__EXPLICIT_MATERIAL_ROLE_BLANK_STEEL_AND_LIGHT_CURTAIN_DIRECTION_PASS__"
        "EXPOSURE_IDENTITY_MECHANICAL_MASS_AND_RELEASE_PRESENTATION_HOLD__RETAINED__NOT_PROMOTED"
        if not failures else "PR009_V085_VISUAL_EVIDENCE_INCOMPLETE__NOT_PROMOTED")
    result = {
        "$schema": "line-boss/audit/press-shop-pr009-visual-v085/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "map": "/Game/LineBoss/Maps/LB_PressShop_PR009LayeredPresentationCandidate_v085",
        "references": {
            "authoritative_pro_sheet_02": {"file": str(REFERENCE), "sha256": sha256(REFERENCE) if REFERENCE.is_file() else None},
            "corrected_source_isometric": {"file": str(SOURCE_REFERENCE), "sha256": sha256(SOURCE_REFERENCE) if SOURCE_REFERENCE.is_file() else None},
        },
        "screenshots": screenshots,
        "human_review": {
            "material_improvements_over_v084": [
                "The blank stack and separator sheets now read as distinct exposed/oiled sheet steel instead of a merged black mass.",
                "Machined rollers and structural steel have useful tonal and roughness separation.",
                "Amber light curtains are now visible and the guarded process is easier to understand.",
                "Charcoal, Cairnwell green, service grey, galvanised mesh and safety-yellow roles are no longer collapsed into the v084 defaults.",
            ],
            "remaining_fails": [
                "The inherited hall/floor response remains over-bright and flattens enclosure depth.",
                "Safety yellow and service grey remain too dominant under the current exposure.",
                "The new identity plate is on the far guard face and is not legible in the fixed management views.",
                "The HMI and local status presentation remain weak at CCTV distance.",
                "The cell still lacks the dense, installed mechanical mass, surface age and service detail of Pro Sheet 02 and the v002 source render.",
                "The elevated camera is still too top-down/blockout-like for release evidence.",
            ],
            "decision": (
                "Retain v085 as a material-role and light-curtain improvement only. Do not promote. "
                "Create isolated v086 with measured near-guard identity placement, darker calibrated material values and improved cameras, then repeat fresh review."
            ),
        },
        "promotion_authorized": False,
        "pr010_started": False,
        "failures": failures,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "failures": failures}, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
