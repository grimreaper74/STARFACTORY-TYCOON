#!/usr/bin/env python3
"""Record the human-reviewed PR-009 v083 fixed-camera decision against Pro Sheet 02."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SCREENSHOTS = ROOT / "Saved/ValidationScreenshots/PressShopIntegration/v083_pr005_runtime"
REFERENCE = ROOT / (
    "SourceAssets/ReferencePacks/CAIRNWELL_PRESS_SHOP_REMAINING_MACHINERY_PACK_v1.0/"
    "visuals/SHEET_02_PR009_ENGINEERING_REFERENCE_4K.png"
)
OUT = ROOT / "Saved/Audits/press_shop_pr009_visual_review_v083.json"
EXPECTED = (
    "press_shop_v083_pr009_process.png",
    "press_shop_v083_pr009_interface.png",
    "press_shop_v083_pr009_cell.png",
    "press_shop_v083_pr009_elevated.png",
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

    result = {
        "$schema": "line-boss/audit/press-shop-pr009-visual-v083/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": (
            "FRESH_FIXED_CAMERA_UNREAL_EVIDENCE_COMPLETE__PRO_SHEET_02_VISUAL_GATE_FAIL__"
            "INTEGRATION_BASELINE_RETAINED__NOT_PROMOTED"
            if not failures else "PR009_V083_VISUAL_EVIDENCE_INCOMPLETE__NOT_PROMOTED"
        ),
        "map": "/Game/LineBoss/Maps/LB_PressShop_PR009PhysicalIntegrationCandidate_v083",
        "reference": {"file": str(REFERENCE), "sha256": sha256(REFERENCE) if REFERENCE.is_file() else None},
        "screenshots": evidence,
        "human_review": {
            "passes": [
                "PR-008 to PR-009 supported roller-transfer span reads continuously in context.",
                "PR-009 guarded-cell footprint, gantry silhouette and material-flow direction are legible.",
                "Open-mesh guarding and control-room-only automation intent remain visible.",
                "No in-world Line Boss branding is visible in the reviewed frames.",
            ],
            "fails": [
                "Machine mass and enclosure depth fall materially short of the Pro Sheet 02 hero target.",
                "Flat, over-bright shared materials read toy-like rather than release-quality industrial finishes.",
                "Gantry, lift-table and output mechanisms need stronger layered framing, actuators and service detail.",
                "White/grey hall context and clipped inherited foreground equipment weaken CCTV composition.",
                "Identity plates are low-contrast or blank at gameplay camera distance.",
                "Moving SK groups remain combined presentation meshes and are not bound to native motion contracts.",
                "Collision candidates are imported evidence only and are not yet bound or runtime-gated.",
            ],
            "decision": "Retain v083 as a technical integration baseline only; create an isolated visual/material/depth iteration before full runtime and promotion gates.",
        },
        "capture_note": "The interface capture produced a valid fresh image before a post-capture Unreal process fault; recapture stability remains a gate.",
        "promotion_authorized": False,
        "failures": failures,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "failures": failures}, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
