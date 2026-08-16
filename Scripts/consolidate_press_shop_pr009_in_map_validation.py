"""Consolidate PR-009 static, PIE, navigation, automation and integrity evidence."""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from press_shop_pr009_in_map_validation_config import TARGET_MAP


ROOT = Path(__file__).resolve().parents[1]
MATCH = re.search(r"_v(\d+)$", TARGET_MAP, re.IGNORECASE)
VERSION = f"v{MATCH.group(1)}" if MATCH else "unknown"
AUDIT_DIR = ROOT / "Saved" / "Audits" / f"PR009_InMap_{VERSION}"
AUTOMATION_DIR = ROOT / "Saved" / "Automation" / f"PR009_InMap_{VERSION}"
OUT = AUDIT_DIR / "PR009_IN_MAP_TECHNICAL_VERIFICATION.json"
REPORT = AUDIT_DIR / "PR009_IN_MAP_TECHNICAL_VERIFICATION_REPORT.md"


def load(path):
    if not path.exists():
        return {"status": "MISSING", "failures": [f"Missing evidence: {path}"]}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def automation(name):
    path = AUTOMATION_DIR / name / "index.json"
    data = load(path)
    passed = data.get("failed") == 0 and data.get("succeeded") == 1 and data.get("notRun") == 0
    tests = [{"path": row.get("fullTestPath"), "state": row.get("state"), "duration": row.get("duration")}
             for row in data.get("tests", [])]
    return {"passed": passed, "report": path.relative_to(ROOT).as_posix(), "summary": {
        "succeeded": data.get("succeeded"), "failed": data.get("failed"), "not_run": data.get("notRun"),
        "tests": tests,
    }}


static = load(AUDIT_DIR / "static_map_audit.json")
runtime = load(AUDIT_DIR / "runtime_pie_audit.json")
navigation = load(AUDIT_DIR / "navigation_pie_audit.json")
navigation_repair = load(AUDIT_DIR / "navigation_coverage_repair.json")
before = load(AUDIT_DIR / "integrity_before.json")
after = load(AUDIT_DIR / "integrity_after.json")
auto_runtime = automation("RuntimeAndSave")
auto_handoff = automation("TraceableBlankHandoff")


def hash_map(data, key):
    return {row["path"]: row["sha256"] for row in data.get(key, [])}


protected_unchanged = hash_map(before, "protected_files") == hash_map(after, "protected_files")
pr010_unchanged = hash_map(before, "pr010_files") == hash_map(after, "pr010_files")

blocked = runtime.get("blocked_transaction", {})
transfers = runtime.get("successful_transfers", [])
motion = runtime.get("motion_checks", {})
save = runtime.get("save_restore", {})
authority = runtime.get("authority_and_isolation", {})
collision = static.get("collision", {})

gates = [
    {
        "id": "G1_NATIVE_CARDINALITY_AND_BINDING",
        "passed": (static.get("native_cardinality", {}).get("pr008_count") == 1
                   and static.get("native_cardinality", {}).get("pr009_count") == 1
                   and static.get("native_cardinality", {}).get("material_flow_count") == 1
                   and static.get("material_flow_binding", {}).get("pr008_matches") is True
                   and static.get("material_flow_binding", {}).get("pr009_matches") is True),
        "evidence": "static_map_audit.json and runtime_pie_audit.json",
    },
    {
        "id": "G2_TRANSACTIONAL_IDENTITY_OWNERSHIP_ROLLBACK_NO_PHANTOMS",
        "passed": (runtime.get("status", "").startswith("PASS") and blocked.get("transfer_rejected") is True
                   and blocked.get("pr008_pending_before") == blocked.get("pr008_pending_after")
                   and blocked.get("pr008_oldest_before") == blocked.get("pr008_oldest_after")
                   and blocked.get("pr009_blank_after") == "None"
                   and blocked.get("pr009_upstream_available_after") is False
                   and len(transfers) == 2
                   and all(row.get("blank_id") == row.get("pr009_owned_blank") for row in transfers)
                   and auto_handoff["passed"]),
        "evidence": "runtime_pie_audit.json plus LineBoss.PressShop.MaterialFlow.PR008ToPR009TraceableBlankHandoff automation",
        "note": "Blocked preflight preserves the exact PR-008 queue and leaves PR-009 empty; controller source restores both snapshots on any post-preflight failure.",
    },
    {
        "id": "G3_NATIVE_PRESENTATION_MOTION_IN_PIE",
        "passed": bool(motion) and all(motion.values()),
        "evidence": "runtime_pie_audit.json transform deltas for rollers, three gantry axes, lift, joggers, separator and output",
    },
    {
        "id": "G4_SAFE_SAVE_LOAD_STOPPED_RESTORE",
        "passed": (save.get("restore_succeeded") is True and "READY" in save.get("restored_state", "").upper()
                   and save.get("restart_required") is True and save.get("maximum_stopped_transform_delta", 999) <= 0.1
                   and save.get("explicit_restart_accepted") is True and auto_runtime["passed"]),
        "evidence": "runtime_pie_audit.json plus LineBoss.PressShop.PR009.RuntimeAndSave automation",
    },
    {
        "id": "G5_REMOTE_AUTHORITY_ISOLATION_ZERO_ENERGY",
        "passed": bool(authority) and all(value for key, value in authority.items()
                   if key.endswith("_rejected") or key.endswith("_accepted")),
        "evidence": "runtime_pie_audit.json",
    },
    {
        "id": "G6_COLLISION_COVERAGE_AND_PROFILE_EVIDENCE",
        "passed": (collision.get("technical_coverage_present") is True
                   and static.get("actor_inventory", {}).get("pr009_static_actor_count") == 10
                   and static.get("actor_inventory", {}).get("pr009_modular_presentation_count") == 158),
        "evidence": "static_map_audit.json",
        "release_collision_ready": collision.get("release_collision_ready", False),
        "classification": "TEMPORARY_COMPLEX_AS_SIMPLE" if collision.get("complex_as_simple_actor_count", 0) else "SIMPLE_COLLISION",
    },
    {
        "id": "G7_RUNTIME_NAVIGATION_AND_PROTECTED_SPACE",
        "passed": (navigation.get("status", "").startswith("PASS")
                   and navigation.get("protected_space_traversal_count") == 0
                   and len(navigation.get("routes", {})) == 2
                   and all(row.get("path_valid") is True and row.get("path_partial") is False
                           for row in navigation.get("routes", {}).values())
                   and navigation_repair.get("area_class") == "/Script/NavigationSystem.NavArea_Null"),
        "evidence": "navigation_pie_audit.json and navigation_coverage_repair.json",
    },
    {
        "id": "G8_ZERO_PR010_AND_PROTECTED_FILE_EDITS",
        "passed": (not static.get("pr010_actor_or_asset_references") and protected_unchanged and pr010_unchanged),
        "evidence": "static_map_audit.json plus integrity_before.json/integrity_after.json",
        "protected_files_unchanged": protected_unchanged,
        "pr010_files_unchanged": pr010_unchanged,
        "pr010_file_count": after.get("pr010_file_count"),
    },
]

failures = [gate["id"] for gate in gates if not gate["passed"]]
payload = {
    "$schema": "cairnwell/audit/press-shop-pr009-in-map-technical-verification/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "target_map_constant": TARGET_MAP,
    "target_version": VERSION,
    "status": "PASS_WITH_RELEASE_COLLISION_REWORK__NOT_PROMOTED" if not failures else "FAIL__NOT_PROMOTED",
    "all_technical_gates_passed": not failures,
    "gates": gates,
    "failed_gates": failures,
    "automation": {"runtime_and_save": auto_runtime, "traceable_blank_handoff": auto_handoff},
    "raw_evidence": {
        "static": "static_map_audit.json", "runtime_pie": "runtime_pie_audit.json",
        "navigation_pie": "navigation_pie_audit.json", "integrity_before": "integrity_before.json",
        "integrity_after": "integrity_after.json", "navigation_coverage_repair": "navigation_coverage_repair.json",
    },
    "scope_exclusions": [
        "No visual material, lighting or camera changes", "No gameplay redesign", "No PR-010 work",
        "No source-staging changes", "No accepted/rejected PR-004 or handoff-document changes", "No promotion",
    ],
    "promotion_authorized": False,
}
AUDIT_DIR.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
report_lines = [
    f"# Cairnwell Press Shop PR-009 {VERSION} technical verification",
    "",
    f"Result: **{payload['status'].replace('_', ' ')}**",
    "",
    f"Target: `{TARGET_MAP}`",
    "",
    "All eight requested technical gates pass in the final clean run:" if not failures
    else f"Failed gates: {', '.join(failures)}",
    "",
]
for index, gate in enumerate(gates, 1):
    report_lines.append(f"{index}. {'PASS' if gate['passed'] else 'FAIL'} - {gate['id']}: {gate['evidence']}")
report_lines += [
    "",
    "Native automation: RuntimeAndSave 1 passed / 0 failed; TraceableBlankHandoff 1 passed / 0 failed."
    if auto_runtime["passed"] and auto_handoff["passed"] else "One or more native automation tests failed.",
    "",
    "The suite is reusable for a later map by changing only `TARGET_MAP` in "
    "`Scripts/press_shop_pr009_in_map_validation_config.py`.",
    "",
    "Promotion remains unauthorized. Release collision remains rework while structural meshes use temporary complex-as-simple collision."
    if not collision.get("release_collision_ready", False) else "Promotion remains unauthorized.",
    "",
]
REPORT.write_text("\n".join(report_lines), encoding="utf-8")
print(json.dumps({"status": payload["status"], "failed_gates": failures, "output": str(OUT)}, indent=2))
raise SystemExit(0 if not failures else 1)
