"""Consolidate exact-map PR-010 v099 technical and visual evidence."""

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "Saved/Audits/PR010_CollisionNavigation"
SHOTS = ROOT / "Saved/ValidationScreenshots/PressShopIntegration/v099_pr010_collision_navigation"
required = {
    "static": AUDIT / "pr010_static_gate_v099.json",
    "collision": AUDIT / "pr010_collision_configuration_v099.json",
    "shuttle": AUDIT / "infeed_shuttle_correction_v099.json",
    "runtime_collision": AUDIT / "runtime_collision_pie_audit_v099.json",
    "navigation": AUDIT / "navigation_pie_audit_v099.json",
}
evidence, failures = {}, []
for name, path in required.items():
    if not path.exists(): failures.append(f"missing {name}"); continue
    row = json.loads(path.read_text(encoding="utf-8")); evidence[name] = row.get("status")
    if not str(row.get("status", "")).startswith("PASS"): failures.append(f"{name} failed")

automations = {}
automation_root = ROOT / "Saved/Automation/PR010_V099_Final"
for name in ("PR010_RuntimeAndSave", "PR009_RuntimeAndSave", "PR008_RuntimeAndSave", "PR008ToPR009TraceableBlankHandoff"):
    path = automation_root / name / "index.json"
    if not path.exists(): failures.append(f"missing automation {name}"); continue
    report = json.loads(path.read_text(encoding="utf-8-sig"))
    automations[name] = {"succeeded": report.get("succeeded"), "failed": report.get("failed"), "warnings": report.get("succeededWithWarnings")}
    if report.get("succeeded") != 1 or report.get("failed") != 0 or report.get("succeededWithWarnings") != 0:
        failures.append(f"automation {name} failed")

screens = []
for name in ("overview", "infeed", "handoff", "service_hmi"):
    path = SHOTS / f"press_shop_v099_pr010_{name}.png"
    screens.append({"view": name, "path": str(path), "exists": path.exists(), "bytes": path.stat().st_size if path.exists() else 0})
    if not path.exists() or path.stat().st_size < 100000: failures.append(f"screenshot {name} missing")

technical = {
    "$schema": "cairnwell/audit/pr010-v099-release-verification/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PR010_V099_EXACT_MAP_COMPILE_STATIC_RUNTIME_SAVE_AUTHORITY_COLLISION_NAVIGATION__VISUAL_RELEASE_HOLD__NOT_PROMOTED" if not failures else "FAIL__PR010_V099_VERIFICATION__NOT_PROMOTED",
    "map": "/Game/LineBoss/Maps/LB_PressShop_PR010CollisionNavigationCandidate_v099",
    "evidence_statuses": evidence, "automations": automations, "screenshots": screens,
    "proved": [
        "Native per-actor roller and reservation-gate pivots; no station-origin orbit.",
        "Fixed 13 m shuttle assembly separated from 2.4 m x 0.8 m moving transfer cradle.",
        "Eight normal stack positions, quality hold, train reservation and lane dispatch.",
        "2,217 runtime frames with all five motion contracts and zero new temporal overlaps.",
        "Moving-state safe restoration and trusted/untrusted remote authority.",
        "58 fixed/detail blockers, 91 query-only moving/material actors and 31 navigation-neutral actors.",
        "Three non-partial autonomous routes avoid the protected buffer volume.",
    ],
    "release_holds": [
        "Carrier, stack, guard and shuttle geometry remains engineering blockout quality.",
        "Open guard rails are collision-correct but visually too heavy and repetitive for release art.",
        "Remote HMI requires final housing, screen UI and control-room interaction presentation.",
        "Hall exposure, floor condition and installed service detail require the shared Press Shop polish pass.",
        "Press Train A-D datums remain TBC and were not invented.",
    ],
    "failures": failures, "promotion_authorized": False,
}
(AUDIT / "PR010_V099_RELEASE_VERIFICATION.json").write_text(json.dumps(technical, indent=2), encoding="utf-8")

visual = {
    "$schema": "cairnwell/audit/pr010-v099-visual-review/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PR010_V099_CORRECTED_SHUTTLE_AND_GUARD_DIRECTION_RETAINED__PRO_SHEET_03_RELEASE_ART_HOLD__NOT_PROMOTED" if not failures else "FAIL__PR010_V099_VISUAL_EVIDENCE__NOT_PROMOTED",
    "authoritative_reference": str(ROOT / "SourceAssets/ReferencePacks/CAIRNWELL_PRESS_SHOP_REMAINING_MACHINERY_PACK_v1.0/visuals/SHEET_03_PR010_ENGINEERING_REFERENCE_4K.png"),
    "reviewed_views": [item["path"] for item in screens],
    "direction_pass": [
        "Four lanes, eight stacks, infeed shuttle, controlled handoff and service-side story remain legible.",
        "Moving transfer cradle now reads independently from the fixed cross-shuttle envelope.",
        "Open rail/end protection sits outside the proved motion envelope.",
        "Cairnwell Automotive, Moorcross Works and PR-010 identity remain legible; no Line Boss branding appears in-world.",
    ],
    "release_art_holds": technical["release_holds"][:4],
    "pro_redesign_required": False, "promotion_authorized": False,
}
(AUDIT / "pr010_visual_review_v099.json").write_text(json.dumps(visual, indent=2), encoding="utf-8")
print(technical["status"])
print(visual["status"])
if failures: raise SystemExit(1)
