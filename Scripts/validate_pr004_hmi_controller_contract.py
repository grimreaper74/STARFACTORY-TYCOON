"""Validate PR-004 shared-cabinet bindings against the controller surface."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "Content/LineBoss/Data/pr004_hmi_controller_contract_v001.json"
HEADER = ROOT / "Source/LineBossCarFactory/LBPR004Station.h"
CONTROLLER_AUDIT = ROOT / "Saved/Audits/pr004_controller_contract_v001_source.json"
OUTPUT = ROOT / "Saved/Audits/pr004_hmi_controller_contract_v001_source.json"


def main() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    header = HEADER.read_text(encoding="utf-8")
    controller_audit = json.loads(CONTROLLER_AUDIT.read_text(encoding="utf-8"))

    calls = sorted({
        action
        for page in contract["pages"]
        for action in page.get("actions", [])
    } | {
        item["controller_call"]
        for item in contract["hardware_platform"]["physical_controls"]
        if "controller_call" in item
    })
    delegates = contract["event_bindings"]
    faults = sorted({fault for values in contract["fault_groups"].values() for fault in values})
    enum_block = header.split("enum class ELBPR004Fault", 1)[1].split("};", 1)[0]
    declared_faults = set(re.findall(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*,?\s*$", enum_block, re.MULTILINE))

    missing_calls = [name for name in calls if not re.search(rf"\b{name}\s*\(", header)]
    missing_delegates = [name for name in delegates if name not in header]
    missing_faults = [name for name in faults if name not in declared_faults]
    ungrouped_faults = sorted(declared_faults - set(faults) - {"None"})
    steps = contract["automatic_sequence"]

    checks = {
        "controller_source_gate_passes": controller_audit.get("status") in {
            "SOURCE_CONTRACT_GATE_PASS_CPP_COMPILE_UNPROVEN",
            "SOURCE_CONTRACT_GATE_PASS_CPP_COMPILE_PASS",
        },
        "shared_physical_cabinet_declared": contract["hardware_platform"]["cabinet"] == "Shared Line Boss HMI Cabinet Platform",
        "downward_screen_orientation_locked": "downward-facing" in contract["hardware_platform"]["screen_orientation"],
        "all_hmi_calls_exist_in_header": not missing_calls,
        "all_event_bindings_exist_in_header": not missing_delegates,
        "every_controller_fault_has_exactly_one_hmi_group": not missing_faults and not ungrouped_faults and len(faults) == len(set(faults)),
        "thirteen_physical_steps_declared_in_order": [item["step"] for item in steps] == list(range(1, 14)),
        "safety_page_is_read_only": next(page for page in contract["pages"] if page["id"] == "SAFETY_INTERLOCKS")["actions"] == [],
        "no_hmi_material_accounting_shortcut": all(
            phrase in contract["player_authority"]["forbidden_shortcuts"]
            for phrase in ["clear a packaging bit from the HMI", "increment waste counts manually"]
        ),
        "manual_recovery_has_all_four_guided_calls": all(
            call in next(page for page in contract["pages"] if page["id"] == "TRAPPED_KEY_RECOVERY")["actions"]
            for call in ["BeginTrappedKeyManualRecovery", "ConfirmTrappedKeyIsolation", "RecordRecoveredWrapFragment", "CompleteTrappedKeyManualRecovery"]
        ),
        "stable_v4_persistence_declared": contract["persistence"]["controller_snapshot"] == "FLBPR004SaveState v4" and contract["persistence"]["stable_only"],
        "promotion_remains_forbidden": contract["implementation_gate"]["promotion"].startswith("FORBIDDEN"),
    }
    passed = all(checks.values())
    result = {
        "$schema": "line-boss/audit/pr004-hmi-controller-source/v1",
        "status": "HMI_SOURCE_CONTRACT_PASS_RUNTIME_UNPROVEN" if passed else "HMI_SOURCE_CONTRACT_FAIL",
        "files": {
            "contract": str(CONTRACT),
            "header": str(HEADER),
            "controller_audit": str(CONTROLLER_AUDIT),
        },
        "checks": checks,
        "missing_calls": missing_calls,
        "missing_delegates": missing_delegates,
        "missing_faults": missing_faults,
        "ungrouped_faults": ungrouped_faults,
        "scope_limit": "Data/header binding validation only; no UMG widget, Unreal compile, runtime or visual claim.",
        "promotion": "FORBIDDEN until compile, Unreal automation, UMG binding and fixed-camera physical-state review pass.",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "checks": checks, "missing_calls": missing_calls, "missing_delegates": missing_delegates, "missing_faults": missing_faults, "ungrouped_faults": ungrouped_faults}, indent=2))
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
