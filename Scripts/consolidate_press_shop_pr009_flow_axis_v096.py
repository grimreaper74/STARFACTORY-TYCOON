"""Consolidate the corrected PR-009 v096 technical and visual release gate."""

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
AUDIT = ROOT / "Saved/Audits/PR009_InMap_v096"
AUTOMATION = ROOT / "Saved/Automation/PR009_InMap_v096"
CAPTURES = ROOT / "Saved/ValidationScreenshots/PressShopIntegration/v096_pr009_enclosure"
OUT = AUDIT / "PR009_FLOW_AXIS_RELEASE_VERIFICATION.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


gate_files = {
    "flow_axis_correction": "flow_axis_correction_build.json",
    "static": "enclosure_release_static_audit.json",
    "runtime_save_authority": "runtime_pie_audit.json",
    "navigation": "navigation_pie_audit.json",
    "physical_shell_door_portals": "enclosure_physical_pie_audit.json",
    "temporal_full_contract_sweeps": "collision_contract_sweep_audit.json",
}
gates = {name: load(AUDIT / filename) for name, filename in gate_files.items()}
automation = {
    name: load(AUTOMATION / name / "index.json")
    for name in ("RuntimeAndSave", "TraceableBlankHandoff")
}

failures = []
for name, payload in gates.items():
    if not str(payload.get("status", "")).startswith("PASS"):
        failures.append(f"{name} status is not PASS")
    if payload.get("failures"):
        failures.append(f"{name} contains failures")
for name, payload in automation.items():
    if payload.get("succeeded") != 1 or payload.get("failed") != 0:
        failures.append(f"{name} automation did not pass exactly 1/1")
    tests = payload.get("tests", [])
    if len(tests) != 1 or tests[0].get("warnings") != 0 or tests[0].get("errors") != 0:
        failures.append(f"{name} automation has warnings/errors or wrong cardinality")

capture_names = [
    "press_shop_v096_pr009_enclosure_hero.png",
    "press_shop_v096_pr009_enclosure_service.png",
    "press_shop_v096_pr009_enclosure_process.png",
    "press_shop_v096_pr009_enclosure_interface.png",
    "press_shop_v096_pr009_enclosure_cell.png",
    "press_shop_v096_pr009_enclosure_elevated.png",
]
captures = []
for name in capture_names:
    path = CAPTURES / name
    exists = path.is_file()
    size = path.stat().st_size if exists else 0
    captures.append({"path": str(path.relative_to(ROOT)), "exists": exists, "bytes": size})
    if not exists or size < 100_000:
        failures.append(f"missing or undersized visual evidence: {name}")

flow = gates["flow_axis_correction"]
if not (224.0 <= flow.get("infeed_mean_world_x_cm", 0) <= 325.0):
    failures.append("corrected PR-009 infeed is outside its audited world-X range")
if not (821.0 <= flow.get("output_mean_world_x_cm", 0) <= 974.0):
    failures.append("corrected PR-009 output is outside its audited world-X range")
if flow.get("expected_pr010_infeed_shuttle_world_x_cm") != 1020.0:
    failures.append("PR-010 handoff datum is not the fixed 1020 cm world-X target")

visual_review = {
    "performed": True,
    "references": [
        "SourceAssets/ReferencePacks/CAIRNWELL_PRESS_SHOP_REMAINING_MACHINERY_PACK_v1.0/visuals/SHEET_02_PR009_ENGINEERING_REFERENCE_4K.png",
        "SourceAssets/PR009/AutomatedBlankStacker/Candidate_v002/PR009_Renders/v002/PR009_v002_isometric_restored.png",
        "SourceAssets/SharedSystems/AutomatedMachineEnclosure/Candidate_v002/renders/CA_MW_ENC_PR009_Pilot_v002_Hero.png",
    ],
    "passes": [
        "Corrected infeed is visibly on the PR-008 side and output is visibly on the PR-010 side.",
        "Enclosed automated-cell silhouette is clear at management-camera distance.",
        "Cairnwell Automotive, Moorcross Works and PR-009 hierarchy is readable on the service face.",
        "External HMI, E-stops, glazing, portals and approved open-mesh transfer guarding remain legible.",
        "Internal conveyors and blank-handling mechanisms remain readable through glazing and process cameras.",
    ],
    "non_blocking_shared_press_shop_polish": [
        "The surrounding hall and floor remain brighter and cleaner than the final Pro condition target.",
        "Close camera views expose intentionally modular geometry; the release target is the seated control-room and CCTV viewing distance.",
        "Factory-wide ageing, installed services and environmental dressing remain a shared Press Shop pass.",
    ],
    "decision": "ACCEPT_PR009_V096_AS_CORRECTED_ENCLOSED_CELL_BASELINE__DO_NOT_CLAIM_FULL_PRESS_SHOP_RELEASE",
}

status = (
    "PASS__PR009_V096_CORRECTED_ENCLOSED_CELL_BASELINE_PROMOTION_AUTHORIZED__PRESS_SHOP_NOT_COMPLETE"
    if not failures else "FAIL__PR009_V096_PROMOTION_NOT_AUTHORIZED"
)
result = {
    "$schema": "cairnwell/audit/pr009-flow-axis-release-verification-v096/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "candidate_map": "/Game/LineBoss/Maps/LB_PressShop_PR009FlowAxisCorrectionCandidate_v096",
    "accepted_map": "/Game/LineBoss/Maps/LB_PressShop_PR009Accepted_v096",
    "status": status,
    "technical_gates": {name: payload.get("status") for name, payload in gates.items()},
    "automations": {
        name: {
            "succeeded": payload.get("succeeded"),
            "failed": payload.get("failed"),
            "warnings": payload.get("tests", [{}])[0].get("warnings"),
            "errors": payload.get("tests", [{}])[0].get("errors"),
        } for name, payload in automation.items()
    },
    "captures": captures,
    "visual_review": visual_review,
    "failures": failures,
    "promotion_authorized": not failures,
    "scope_limit": "PR-009 corrected enclosed-cell baseline only; neither the full Press Shop nor the game is complete.",
}
OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps({"status": status, "output": str(OUT), "failures": failures}, indent=2))
if failures:
    raise SystemExit(1)
