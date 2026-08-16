#!/usr/bin/env python3
"""Record the human-reviewed PR-009 v087 visual/collision decision."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SCREENSHOTS = ROOT / "Saved/ValidationScreenshots/PressShopIntegration/v087_pr009_release_collision"
REFERENCE = ROOT / (
    "SourceAssets/ReferencePacks/CAIRNWELL_PRESS_SHOP_REMAINING_MACHINERY_PACK_v1.0/"
    "visuals/SHEET_02_PR009_ENGINEERING_REFERENCE_4K.png")
SOURCE_REFERENCE = Path(
    r"C:\Users\greg_\Projects\LineBoss_PR009_PR010_Staging\PR009_Renders\v002"
    r"\PR009_v002_isometric_restored.png")
STATIC = ROOT / "Saved/Audits/PR009_InMap_v087/release_collision_static_audit.json"
PHYSICAL = ROOT / "Saved/Audits/PR009_InMap_v087/physical_collision_pie_audit.json"
SWEEPS = ROOT / "Saved/Audits/PR009_InMap_v087/collision_contract_sweep_audit.json"
OUT = ROOT / "Saved/Audits/press_shop_pr009_visual_review_v087.json"
EXPECTED = tuple(
    f"press_shop_v087_pr009_release_collision_{name}.png"
    for name in ("process", "interface", "cell", "elevated"))


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
    required = (
        ("Pro Sheet 02", REFERENCE),
        ("corrected v002 source render", SOURCE_REFERENCE),
        ("v087 static collision audit", STATIC),
        ("v087 physical collision audit", PHYSICAL),
        ("v087 full-contract sweep audit", SWEEPS),
    )
    for label, path in required:
        if not path.is_file():
            failures.append(f"Missing {label}")

    raw = {}
    for label, path in (("static", STATIC), ("physical", PHYSICAL), ("sweeps", SWEEPS)):
        if path.is_file():
            raw[label] = json.loads(path.read_text(encoding="utf-8"))
    collision_release_ready = (
        raw.get("static", {}).get("asset_collision_ready") is True
        and raw.get("physical", {}).get("status", "").startswith("PASS")
        and raw.get("sweeps", {}).get("status", "").startswith("PASS"))

    status = (
        "FRESH_FIXED_CAMERA_UNREAL_EVIDENCE_COMPLETE__V086_VISUAL_INVARIANT_AND_AUTHORED_SIMPLE_COLLISION_DIRECTION_PASS__"
        "FULL_SIZE_BLANK_AND_FULL_GANTRY_TRACE_PORTAL_CLEARANCE_FAIL__EXISTING_VISUAL_RELEASE_HOLDS_REMAIN__RETAINED__NOT_PROMOTED"
        if not failures else "PR009_V087_VISUAL_EVIDENCE_INCOMPLETE__NOT_PROMOTED")
    payload = {
        "$schema": "line-boss/audit/press-shop-pr009-visual-v087/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "map": "/Game/LineBoss/Maps/LB_PressShop_PR009ReleaseCollisionCandidate_v087",
        "references": {
            "authoritative_pro_sheet_02": {"file": str(REFERENCE), "sha256": sha256(REFERENCE) if REFERENCE.is_file() else None},
            "corrected_source_isometric": {"file": str(SOURCE_REFERENCE), "sha256": sha256(SOURCE_REFERENCE) if SOURCE_REFERENCE.is_file() else None},
        },
        "screenshots": screenshots,
        "human_review": {
            "passes": [
                "The invisible collision authoring preserves the retained v086 material, lighting, camera and identity presentation.",
                "All four fixed-camera frames remain visually consistent with the retained v086 checkpoint.",
                "Open-mesh guarding, blank steel, amber light curtains and the calibrated material hierarchy remain readable.",
            ],
            "collision_design_fails": [
                "The full 1800 x 2600 mm blank envelope is blocked at the trace portal because its authored clear opening is exactly 2600 mm with no operating clearance.",
                "The authoritative 2800 mm gantry bridge travel intersects the trace-portal beam and both posts, although the current 700 mm recipe motion does not reach them.",
                "The trace portal must be moved toward the output and rebuilt with a wider clear opening in an isolated successor; reducing the authoritative gantry contract is not accepted.",
            ],
            "existing_visual_holds": [
                "Identity typography remains too small and soft at the fixed management-camera distance.",
                "All current cameras remain on the opposite side from the authored HMI and electrical cabinet.",
                "The hall/floor and installed service presentation remain too clean, bright and sparse compared with Pro Sheet 02.",
                "The interface and elevated frames still read as technical validation views rather than final management-game presentation.",
            ],
            "decision": (
                "Retain v087 only as an authored-simple-collision checkpoint. Do not promote. Build an isolated successor with a dimensioned "
                "relocated/widened trace portal, then rerun full-size material, full-contract motion/collision, all runtime gates and fresh visual review."
            ),
        },
        "collision_evidence": {
            label: {"file": str(path), "sha256": sha256(path) if path.is_file() else None,
                    "status": raw.get(label, {}).get("status")}
            for label, path in (("static", STATIC), ("physical", PHYSICAL), ("sweeps", SWEEPS))
        },
        "release_collision_ready": collision_release_ready,
        "promotion_authorized": False,
        "pr010_started": False,
        "failures": failures,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": status,
        "release_collision_ready": collision_release_ready,
        "failures": failures,
    }, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
