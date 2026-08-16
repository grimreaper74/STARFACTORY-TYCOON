"""Static gate for the native PR-005 HMI widget; never claims a successful compile."""

from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
HEADER = ROOT / "Source/LineBossCarFactory/LBPR005HMIWidget.h"
CPP = ROOT / "Source/LineBossCarFactory/LBPR005HMIWidget.cpp"
CONTRACT = ROOT / "Content/LineBoss/Data/pr005_hmi_controller_contract_v001.json"
OUTPUT = ROOT / "Saved/Audits/pr005_hmi_widget_source_v001.json"

header = HEADER.read_text(encoding="utf-8")
cpp = CPP.read_text(encoding="utf-8")
contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
failures = []

required_methods = [
    "BindStation", "HandlePhysicalControlPower", "HandlePhysicalModeSelection",
    "HandlePhysicalCycleStart", "HandlePhysicalControlledStop",
    "HandlePhysicalFaultReset", "BuildScreen", "RefreshFromStation"
]
for method in required_methods:
    if not re.search(rf"\b{method}\s*\(", header):
        failures.append(f"missing declaration {method}")
    if not re.search(rf"ULBPR005HMIWidget::{method}\s*\(", cpp):
        failures.append(f"missing definition {method}")

required_controller_calls = {
    "HandlePhysicalControlPower": "SetControlPower",
    "HandlePhysicalModeSelection": "SetControlMode",
    "HandlePhysicalCycleStart": "PressCycleStart",
    "HandlePhysicalControlledStop": "RequestControlledStop",
    "HandlePhysicalFaultReset": "ResetFault",
    "RefreshFromStation": "GetHMIStatus",
}
for widget_method, controller_call in required_controller_calls.items():
    if controller_call not in cpp:
        failures.append(f"{widget_method} does not reference {controller_call}")

for forbidden in ["Checklist.", "MachineState =", "bSafetyCircuitReset =", "bGuardsClosed ="]:
    if forbidden in cpp:
        failures.append(f"widget directly mutates or reaches into protected controller state: {forbidden}")

e_stop = next(x for x in contract["hardware_platform"]["physical_controls"] if x["id"] == "EMERGENCY_STOP")
if e_stop["controller_call"] is not None:
    failures.append("contract exposes emergency stop as a software command")
if "EmergencyStop" in header or "EmergencyStop" in cpp:
    failures.append("widget exposes a software emergency-stop implementation")

result = {
    "status": "PASS_SOURCE_ONLY_COMPILE_RUNTIME_UNPROVEN" if not failures else "FAIL",
    "widget_header": str(HEADER.relative_to(ROOT)).replace("\\", "/"),
    "widget_implementation": str(CPP.relative_to(ROOT)).replace("\\", "/"),
    "contract": str(CONTRACT.relative_to(ROOT)).replace("\\", "/"),
    "required_methods": required_methods,
    "controller_routing": required_controller_calls,
    "screen_refresh_hz": contract["data_projection"]["refresh_hz"],
    "failures": failures,
    "scope_limit": "Source routing/safety audit only; UHT, C++ compile, UMG construction, WidgetComponent input and runtime behavior remain unproven.",
    "promotion": False,
}
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result, indent=2))
raise SystemExit(1 if failures else 0)
