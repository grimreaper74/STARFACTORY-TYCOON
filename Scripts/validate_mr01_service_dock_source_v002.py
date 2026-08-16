"""Validate MR01 dock v002 by extending the exact v001 source gate."""
from __future__ import annotations

import importlib.util
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import bpy


def load_validator(path: Path):
    spec = importlib.util.spec_from_file_location("lb_mr01_dock_v001_validator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load validator: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if not args:
        raise SystemExit("Output JSON path required")
    output = Path(args[0]).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    base_output = output.with_name(output.stem + "_base_v001.tmp.json")
    validator_path = Path(__file__).with_name("validate_mr01_service_dock_source_v001.py")
    validator = load_validator(validator_path)
    saved_argv = list(sys.argv)
    try:
        sys.argv = [str(validator_path), "--", str(base_output)]
        validator.main()
    finally:
        sys.argv = saved_argv
    payload = json.loads(base_output.read_text(encoding="utf-8"))
    base_output.unlink(missing_ok=True)

    objects = bpy.data.objects
    failures = list(payload.get("failures", []))
    required = [
        "ROOT_LB_MR01_SERVICE_DOCK_V002",
        "SM_LB_MR01_ToolRack_BackPanel", "SM_LB_MR01_ToolRack_Side_L",
        "SM_LB_MR01_ToolRack_Side_R", "SM_LB_MR01_ToolRack_Top", "SM_LB_MR01_ToolRack_Sill",
        "SM_LB_MR01_Consumables_BackPanel", "SM_LB_MR01_Consumables_Side_L",
        "SM_LB_MR01_Consumables_Side_R", "SM_LB_MR01_Consumables_Top",
        "SM_LB_MR01_DockIdentityPlate", "TXT_LB_MR01_DockIdentityMounted",
    ]
    missing = [name for name in required if name not in objects]
    if missing:
        failures.append(f"missing v002 detail objects: {missing}")
    forbidden_solids = [name for name in (
        "SM_LB_MR01_DockToolRackCabinet", "SM_LB_MR01_DockConsumablesCabinet"
    ) if name in objects]
    if forbidden_solids:
        failures.append(f"visually rejected solid cabinets remain: {forbidden_solids}")

    mounted_labels = sorted(obj.name for obj in objects if re.match(r"^TXT_LB_MR01_ToolMounted_\d\d$", obj.name))
    plaques = sorted(obj.name for obj in objects if re.match(r"^SM_LB_MR01_ToolPlaque_\d\d$", obj.name))
    consumables = sorted(obj.name for obj in objects if re.match(r"^SM_LB_MR01_ConsumableModule_\d\d$", obj.name))
    if len(mounted_labels) != 8 or len(plaques) != 8:
        failures.append(f"mounted tool identity count mismatch: labels={len(mounted_labels)}, plaques={len(plaques)}")
    if len(consumables) != 8:
        failures.append(f"expected eight visible consumable/service modules, found {len(consumables)}")

    payload.update({
        "$schema": "cairnwell/validation/mr01-service-dock-source-v002/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS__V002_EXACT_INTERFACES_OPEN_FABRICATED_CABINETS_VISIBLE_EIGHT_TOOL_RACK__VISUAL_UNREAL_RUNTIME_GATES_OPEN__NOT_PROMOTED" if not failures else "FAIL__SOURCE_GATE",
        "v002_required_objects": required,
        "v002_missing_objects": missing,
        "v002_forbidden_solid_cabinets": forbidden_solids,
        "v002_mounted_tool_labels": mounted_labels,
        "v002_tool_plaques": plaques,
        "v002_visible_consumable_modules": consumables,
        "failures": failures,
        "promotion_authorized": False,
    })
    payload["holds"] = [
        "Visual fixed-camera inspection must pass before Unreal intake.",
        "Actual MR01 v021 docked fit, clean export/reimport, Unreal collision, navigation, charging/runtime and service-sweep gates remain open.",
        "Two Press Shop MR01 berth instances are required; the capacity study does not install or promote them.",
    ]
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"status": payload["status"], "failures": failures}, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
