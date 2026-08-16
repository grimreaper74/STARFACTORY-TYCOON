"""Consolidate the final technical and visual PR-009 v095 enclosure gate."""

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
AUDIT = ROOT / "Saved/Audits/PR009_InMap_v095"
AUTOMATION = ROOT / "Saved/Automation/PR009_InMap_v095"
CAPTURES = ROOT / "Saved/ValidationScreenshots/PressShopIntegration/v095_pr009_enclosure"
OUT = AUDIT / "PR009_ENCLOSURE_RELEASE_VERIFICATION.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


gate_files = {
    "static": "enclosure_release_static_audit.json",
    "runtime_save_authority": "runtime_pie_audit.json",
    "navigation": "navigation_pie_audit.json",
    "physical_shell_door_portals": "enclosure_physical_pie_audit.json",
    "full_contract_sweeps": "collision_contract_sweep_audit.json",
}
gates = {name: load(AUDIT / filename) for name, filename in gate_files.items()}
automation = {
    name: load(AUTOMATION / name / "index.json")
    for name in ("RuntimeAndSave", "TraceableBlankHandoff")
}
before = load(AUDIT / "integrity_gate_before.json")
after = load(AUDIT / "integrity_gate_after.json")

failures = []
for name, payload in gates.items():
    if not str(payload.get("status", "")).startswith("PASS"):
        failures.append(f"{name} status is not PASS")
    if payload.get("failures"):
        failures.append(f"{name} contains failures")
for name, payload in automation.items():
    if payload.get("succeeded") != 1 or payload.get("failed") != 0:
        failures.append(f"{name} automation did not pass exactly 1/1")
    test_rows = payload.get("tests", [])
    if len(test_rows) != 1 or test_rows[0].get("warnings") != 0 or test_rows[0].get("errors") != 0:
        failures.append(f"{name} automation has warnings/errors or wrong cardinality")
for scope in ("protected_files", "source_files", "robot_files", "pr010_files"):
    if before.get(scope) != after.get(scope):
        failures.append(f"integrity scope changed: {scope}")

capture_names = [
    "press_shop_v095_pr009_enclosure_hero.png",
    "press_shop_v095_pr009_enclosure_service.png",
    "press_shop_v095_pr009_enclosure_process.png",
    "press_shop_v095_pr009_enclosure_interface.png",
    "press_shop_v095_pr009_enclosure_cell.png",
    "press_shop_v095_pr009_enclosure_elevated.png",
    "press_shop_v095_pr009_service_door_open_pie.png",
]
capture_rows = []
for name in capture_names:
    path = CAPTURES / name
    exists = path.is_file()
    size = path.stat().st_size if exists else 0
    capture_rows.append({"path": str(path.relative_to(ROOT)), "exists": exists, "bytes": size})
    if not exists or size < 100_000:
        failures.append(f"missing or undersized visual evidence: {name}")

visual_review = {
    "performed": True,
    "references": [
        "SourceAssets/ReferencePacks/CAIRNWELL_PRESS_SHOP_REMAINING_MACHINERY_PACK_v1.0/visuals/SHEET_02_PR009_ENGINEERING_REFERENCE_4K.png",
        "SourceAssets/PR009/AutomatedBlankStacker/Candidate_v002/PR009_Renders/v002/PR009_v002_isometric_restored.png",
        "SourceAssets/SharedSystems/AutomatedMachineEnclosure/Candidate_v002/renders/CA_MW_ENC_PR009_Pilot_v002_Hero.png",
    ],
    "passes": [
        "Enclosed automated-cell silhouette is clear at management-camera distance.",
        "Controlled infeed/outfeed portals remain visibly open and mechanically connected.",
        "Cairnwell Automotive, Moorcross Works and PR-009 hierarchy is readable on the service/hero face.",
        "External HMI, electrical/service cabinet, E-stops, glazing and approved open-mesh transfer guarding remain legible.",
        "Validated internal conveyors, gantry and blank handling remain deliberately visible through glazing and process cameras.",
    ],
    "remaining_press_shop_polish": [
        "The surrounding hall exposure and service-grey roof response remain brighter and cleaner than the Pro condition target.",
        "Factory-wide floor ageing, installed services and environmental dressing remain a later shared Press Shop pass.",
    ],
    "decision": "ACCEPT_PR009_V095_AS_ENCLOSED_CELL_BASELINE__DO_NOT_CLAIM_FULL_PRESS_SHOP_RELEASE",
}

status = (
    "PASS__PR009_V095_ENCLOSED_CELL_BASELINE_PROMOTION_AUTHORIZED__PRESS_SHOP_NOT_COMPLETE"
    if not failures
    else "FAIL__PR009_V095_PROMOTION_NOT_AUTHORIZED"
)
result = {
    "$schema": "cairnwell/audit/pr009-enclosure-release-verification-v095/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "candidate_map": "/Game/LineBoss/Maps/LB_PressShop_PR009EnclosureReleaseCandidate_v095",
    "accepted_map": "/Game/LineBoss/Maps/LB_PressShop_PR009Accepted_v095",
    "status": status,
    "technical_gates": {name: payload.get("status") for name, payload in gates.items()},
    "automations": {
        name: {
            "succeeded": payload.get("succeeded"),
            "failed": payload.get("failed"),
            "warnings": payload.get("tests", [{}])[0].get("warnings"),
            "errors": payload.get("tests", [{}])[0].get("errors"),
        }
        for name, payload in automation.items()
    },
    "integrity": {
        scope: {"match": before.get(scope) == after.get(scope), "count": len(before.get(scope, []))}
        for scope in ("protected_files", "source_files", "robot_files", "pr010_files")
    },
    "captures": capture_rows,
    "visual_review": visual_review,
    "failures": failures,
    "promotion_authorized": not failures,
    "scope_limit": "PR-009 enclosed-cell baseline only; neither the full Press Shop nor the game is complete.",
}
OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps({"status": status, "output": str(OUT), "failures": failures}, indent=2))
if failures:
    raise SystemExit(1)
