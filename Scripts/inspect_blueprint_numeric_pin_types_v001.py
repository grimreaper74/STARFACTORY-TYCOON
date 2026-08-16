"""Inspect UE 5.8 Blueprint numeric pin names and live v020 state types."""

import json
from pathlib import Path

import unreal


root = Path(unreal.Paths.project_dir())
output = root / "Saved/Audits/blueprint_numeric_pin_types_v001.json"
bp_path = "/Game/LineBoss/Equipment/Robots/Modular6Axis/Candidate_v020/BP_LB_Modular6AxisRobot_400kg_v020"
bp = unreal.EditorAssetLibrary.load_asset(bp_path)
pin_types = {}
for name in ("float", "double", "real", "int", "int64", "bool", "string"):
    try:
        pin = unreal.BlueprintEditorLibrary.get_basic_type_by_name(name)
        pin_types[name] = {
            "export": pin.export_text(),
            "dict": pin.to_dict(),
        }
    except Exception as exc:
        pin_types[name] = {"error": repr(exc)}

generated = unreal.BlueprintEditorLibrary.generated_class(bp)
default = unreal.get_default_object(generated)
values = {}
for name in (
    "ConditionAgeYears",
    "J1Degrees",
    "OperatingHours",
    "ConditionSeed",
    "ServiceCycles",
):
    try:
        value = default.get_editor_property(name)
        values[name] = {"python_type": str(type(value)), "value": value}
    except Exception as exc:
        values[name] = {"error": repr(exc)}

payload = {
    "engine": str(unreal.SystemLibrary.get_engine_version()),
    "blueprint": bp_path,
    "pin_types": pin_types,
    "default_values": values,
}
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_BLUEPRINT_NUMERIC_PIN_TYPES_V001_PASS audit={output}")
unreal.SystemLibrary.quit_editor()
