"""Consolidate PR-010 v098 evidence without authorizing promotion."""

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "Saved/Audits/PR010_DetailedRuntime"
SHOTS = ROOT / "Saved/ValidationScreenshots/PressShopIntegration/v098_pr010_detailed_runtime"
static = json.loads((AUDIT / "pr010_static_gate_v098.json").read_text(encoding="utf-8"))
build = json.loads((AUDIT / "pr010_detailed_runtime_build_v098.json").read_text(encoding="utf-8"))

automation_paths = {
    "pr010_runtime_and_save": ROOT / "Saved/Automation/PR010_Runtime_v001/index.json",
    "pr008_runtime_and_save": ROOT / "Saved/Automation/PR010_Regression_v001/PR008_RuntimeAndSave/index.json",
    "pr009_runtime_and_save": ROOT / "Saved/Automation/PR010_Regression_v001/PR009_RuntimeAndSave/index.json",
    "pr008_to_pr009_traceable_handoff": ROOT / "Saved/Automation/PR010_Regression_v001/PR008ToPR009TraceableBlankHandoff/index.json",
}
automations = {}
failures = []
for name, path in automation_paths.items():
    if not path.exists():
        failures.append(f"missing automation report: {name}")
        continue
    report = json.loads(path.read_text(encoding="utf-8-sig"))
    automations[name] = {"succeeded": report.get("succeeded"), "failed": report.get("failed"), "warnings": report.get("succeededWithWarnings")}
    if report.get("succeeded") != 1 or report.get("failed") != 0 or report.get("succeededWithWarnings") != 0:
        failures.append(f"automation gate failed: {name}")

screens = []
for name in ("overview", "infeed", "handoff", "service_hmi"):
    path = SHOTS / f"press_shop_v098_pr010_{name}.png"
    screens.append({"view": name, "path": str(path), "exists": path.exists(), "bytes": path.stat().st_size if path.exists() else 0})
    if not path.exists() or path.stat().st_size < 100000:
        failures.append(f"fresh screenshot missing or undersized: {name}")

if not str(static.get("status", "")).startswith("PASS"):
    failures.append("static gate failed")
if not str(build.get("status", "")).startswith("PASS"):
    failures.append("build gate failed")

technical = {
    "$schema": "cairnwell/audit/pr010-detailed-runtime-verification-v098/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PR010_V098_NATIVE_RUNTIME_STATIC_AUTOMATION_AND_FRESH_EVIDENCE__COLLISION_NAV_RELEASE_GATES_REMAIN__NOT_PROMOTED" if not failures else "FAIL__PR010_V098_VERIFICATION__NOT_PROMOTED",
    "map": "/Game/LineBoss/Maps/LB_PressShop_PR010DetailedRuntimeCandidate_v098",
    "native_runtime": {
        "four_lane_capacity": 8,
        "deterministic_lane_allocation": True,
        "fifo_dispatch": True,
        "remote_authority": "CW.MW.CONTROL_ROOM",
        "safe_save_restore": True,
        "moving_part_bindings": len(build.get("moving_presentation_bindings", [])),
    },
    "automations": automations,
    "screenshots": screens,
    "release_holds": [
        "Inherited 142-object engineering blockout remains NoCollision/navigation-neutral.",
        "Final collision contracts, robot-route navigation and temporal moving-part sweeps have not passed.",
        "Geometry remains engineering-detail quality and needs final modular mesh/material polish.",
        "Press-train datums remain TBC and were not invented.",
    ],
    "failures": failures,
    "promotion_authorized": False,
}
(AUDIT / "PR010_V098_RELEASE_VERIFICATION.json").write_text(json.dumps(technical, indent=2), encoding="utf-8")

visual = {
    "$schema": "cairnwell/audit/pr010-detailed-runtime-visual-review-v098/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PR010_V098_RETAINED_DETAILED_RUNTIME_DIRECTION__NOT_RELEASE_ART__NOT_PROMOTED" if not failures else "FAIL__PR010_V098_VISUAL_EVIDENCE__NOT_PROMOTED",
    "reviewed_views": [item["path"] for item in screens],
    "accepted_direction": [
        "Four-lane buffer reads clearly from the fixed overview.",
        "PR-009 to PR-010 material-flow interface remains visible.",
        "Inspection glazing no longer reads as an opaque wall.",
        "Controlled task lighting makes carriers, stacks and safety edges readable.",
        "Cairnwell Automotive, Moorcross Works and PR-010 identity is mounted and legible.",
    ],
    "visual_holds": [
        "Blank stacks and carrier forms remain coarse blockout geometry.",
        "Open safety hardware is directionally correct but not final mesh/detail quality.",
        "Service HMI is readable evidence but requires final screen UI and housing art.",
        "Hall lighting and camera composition need final Press Shop-wide balancing.",
    ],
    "pro_redesign_required": False,
    "promotion_authorized": False,
}
(AUDIT / "pr010_visual_review_v098.json").write_text(json.dumps(visual, indent=2), encoding="utf-8")

print(technical["status"])
print(visual["status"])
if failures:
    raise SystemExit(1)
