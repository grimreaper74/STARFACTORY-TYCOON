"""Validate the PR-005 shared-HMI source contract without claiming runtime proof."""

from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
HEADER = ROOT / "Source/LineBossCarFactory/LBPR005Station.h"
CPP = ROOT / "Source/LineBossCarFactory/LBPR005Station.cpp"
CONTRACT = ROOT / "Content/LineBoss/Data/pr005_hmi_controller_contract_v001.json"
OUTPUT = ROOT / "Saved/Audits/pr005_hmi_controller_contract_v001.json"

header = HEADER.read_text(encoding="utf-8")
cpp = CPP.read_text(encoding="utf-8")
contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
failures = []

required_types = ["ELBPR005ControlMode", "FLBPR005HMIStatus"]
required_calls = sorted({
    item["controller_call"]
    for item in contract["hardware_platform"]["physical_controls"]
    if item.get("controller_call")
} | {contract["data_projection"]["controller_getter"]})
for token in required_types:
    if token not in header:
        failures.append(f"missing type {token}")
for call in required_calls:
    if not re.search(rf"\b{re.escape(call)}\s*\(", header):
        failures.append(f"missing declaration {call}")
    if not re.search(rf"ALBPR005Station::{re.escape(call)}\s*\(", cpp):
        failures.append(f"missing definition {call}")
for field in contract["data_projection"]["fields"]:
    if not re.search(rf"\b{re.escape(field)}\b", header):
        failures.append(f"HMI status field absent from header: {field}")
for field in contract["persistence"]["savegame_fields"]:
    pattern = rf"UPROPERTY\([^)]*SaveGame[^)]*\)[\s\S]{{0,180}}\b{re.escape(field)}\b"
    if not re.search(pattern, header):
        failures.append(f"SaveGame field not proven: {field}")

safety_checks = {
    "power_off_forces_mode_off": "ControlMode = ELBPR005ControlMode::Off" in cpp,
    "cycle_start_checks_fault": "ActiveFault != ELBPR005Fault::None" in cpp,
    "manual_dry_cycle_only": "ControlMode == ELBPR005ControlMode::Manual && BeginDryCycle()" in cpp,
    "automatic_certified_run_only": "ControlMode == ELBPR005ControlMode::Automatic && StartAutomaticProduction()" in cpp,
    "reset_checks_guards_and_safety": "!Checklist.bGuardsClosed || !Checklist.bSafetyCircuitReset" in cpp,
    "e_stop_not_software_action": next(x for x in contract["hardware_platform"]["physical_controls"] if x["id"] == "EMERGENCY_STOP")["controller_call"] is None,
}
failures.extend(f"safety invariant failed: {name}" for name, passed in safety_checks.items() if not passed)

result = {
    "status": "PASS_SOURCE_ONLY_RUNTIME_UNPROVEN" if not failures else "FAIL",
    "contract": str(CONTRACT.relative_to(ROOT)).replace("\\", "/"),
    "header": str(HEADER.relative_to(ROOT)).replace("\\", "/"),
    "implementation": str(CPP.relative_to(ROOT)).replace("\\", "/"),
    "required_calls": required_calls,
    "hmi_field_count": len(contract["data_projection"]["fields"]),
    "page_count": len(contract["pages"]),
    "safety_checks": safety_checks,
    "failures": failures,
    "scope_limit": "Static source/contract validation only; no UHT, compile, UMG, runtime, interaction or SaveGame execution claim.",
    "promotion": False,
}
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result, indent=2))
raise SystemExit(1 if failures else 0)
