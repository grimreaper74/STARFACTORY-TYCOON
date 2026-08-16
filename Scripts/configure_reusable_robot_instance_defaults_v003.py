"""Set and audit defaults for the reusable modular robot instance-state contract."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BP_PATH = "/Game/LineBoss/Equipment/Robots/Modular6Axis/Candidate_v005/BP_LB_Modular6AxisRobot_400kg_v005"
AUDIT = ROOT / "Saved/Audits/reusable_modular_robot_instance_defaults_v005.json"
lib = unreal.EditorAssetLibrary
bp_lib = unreal.BlueprintEditorLibrary
bp = lib.load_asset(BP_PATH)
if bp is None:
    raise RuntimeError(f"Missing {BP_PATH}")

defaults = {
    "StationId": "UNASSIGNED",
    "EquipmentId": "ROBOT-UNASSIGNED",
    "ConditionAgeYears": 7.0,
    "ConditionSeed": 0,
    "CurrentToolId": "BandCutterCapture",
    "J1Degrees": 0.0,
    "J2Degrees": 0.0,
    "J3Degrees": 0.0,
    "J4Degrees": 0.0,
    "J5Degrees": 0.0,
    "J6Degrees": 0.0,
    "Enabled": False,
    "ToolLocked": False,
    "FaultCode": "NONE",
    "OperatingHours": 0.0,
    "ServiceCycles": 0,
}

bp_lib.compile_blueprint(bp)
generated_class = bp_lib.generated_class(bp)
cdo = unreal.get_default_object(generated_class)
written = {}
for name, value in defaults.items():
    cdo.set_editor_property(name, value)
    written[name] = cdo.get_editor_property(name)
bp_lib.compile_blueprint(bp)
if not lib.save_loaded_asset(bp, only_if_is_dirty=False):
    raise RuntimeError(f"Could not save {BP_PATH}")

# Re-read the compiled default object after saving.
generated_class = bp_lib.generated_class(bp)
cdo = unreal.get_default_object(generated_class)
verified = {name: cdo.get_editor_property(name) for name in defaults}
members = [str(name) for name in bp_lib.list_member_variable_names(bp)]
missing = sorted(set(defaults) - set(members))
if missing:
    raise RuntimeError(f"Compiled Blueprint is missing state variables: {missing}")

payload = {
    "$schema": "line-boss/audit/reusable-modular-robot-instance-defaults-v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "INSTANCE_VARIABLES_AND_DEFAULTS_COMPILED__RUNTIME_BINDING_OPEN__NOT_PROMOTED",
    "blueprint": BP_PATH,
    "member_variables": members,
    "requested_defaults": defaults,
    "verified_defaults": verified,
    "missing_variables": missing,
    "runtime_save_binding_gate": "OPEN",
    "construction_joint_binding_gate": "OPEN",
    "promotion_authorized": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_REUSABLE_ROBOT_DEFAULTS_V003_PASS variables={len(defaults)} audit={AUDIT}")
unreal.SystemLibrary.quit_editor()
