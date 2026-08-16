"""Repair v020 Blueprint numeric state variables to UE 5.8 real/double pins."""

from datetime import datetime, timezone
import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BP_PATH = "/Game/LineBoss/Equipment/Robots/Modular6Axis/Candidate_v020/BP_LB_Modular6AxisRobot_400kg_v020"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004SurfaceForgeRobotCandidate_v020"
ROBOT_LABEL = "LB_INT_PR004_BP_ModularRobot_400kg_v020"
BUILD_AUDIT = ROOT / "Saved/Audits/press_shop_pr004_surfaceforge_robot_candidate_v020.json"
REPAIR_AUDIT = ROOT / "Saved/Audits/press_shop_pr004_surfaceforge_robot_numeric_state_repair_v020.json"

REAL_VARIABLES = {
    "ConditionAgeYears": 7.0,
    "J1Degrees": 0.0,
    "J2Degrees": 0.0,
    "J3Degrees": 0.0,
    "J4Degrees": 0.0,
    "J5Degrees": 0.0,
    "J6Degrees": 0.0,
    "OperatingHours": 18420.0,
}

lib = unreal.EditorAssetLibrary
bp_lib = unreal.BlueprintEditorLibrary
blueprint = lib.load_asset(BP_PATH)
if blueprint is None:
    raise RuntimeError(f"Missing generated v020 Blueprint {BP_PATH}")

for name in REAL_VARIABLES:
    bp_lib.remove_member_variable(blueprint, name)

real_pin = bp_lib.get_basic_type_by_name("real")
for name in REAL_VARIABLES:
    if not bp_lib.add_member_variable(blueprint, name, real_pin):
        raise RuntimeError(f"Could not re-add {name} as a UE real pin")
    bp_lib.set_blueprint_variable_instance_editable(blueprint, name, True)

bp_lib.compile_blueprint(blueprint)
if not lib.save_loaded_asset(blueprint, only_if_is_dirty=False):
    raise RuntimeError("Could not save repaired v020 Blueprint")

generated = bp_lib.generated_class(blueprint)
default = unreal.get_default_object(generated)
default_types = {name: str(type(default.get_editor_property(name))) for name in REAL_VARIABLES}
if any(value != "<class 'float'>" for value in default_types.values()):
    raise RuntimeError(f"Numeric type repair failed: {default_types}")

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
robots = [actor for actor in actors.get_all_level_actors() if actor.get_actor_label() == ROBOT_LABEL]
if len(robots) != 1:
    raise RuntimeError(f"Expected one v020 robot, found {len(robots)}")
robot = robots[0]
for name, value in REAL_VARIABLES.items():
    robot.set_editor_property(name, value)
verified_values = {name: robot.get_editor_property(name) for name in REAL_VARIABLES}
verified_types = {name: str(type(value)) for name, value in verified_values.items()}
if verified_values != REAL_VARIABLES or any(value != "<class 'float'>" for value in verified_types.values()):
    raise RuntimeError(f"Live numeric state repair failed: values={verified_values} types={verified_types}")
if not levels.save_current_level():
    raise RuntimeError(f"Could not save repaired map {MAP}")

build_payload = json.loads(BUILD_AUDIT.read_text(encoding="utf-8"))
for row in build_payload["instance_variables"]:
    if row["name"] in REAL_VARIABLES:
        row["type"] = "real"
build_payload["instance_state"].update(verified_values)
build_payload["numeric_state_gate"] = {
    "status": "PASS",
    "ue_pin_category": "real",
    "ue_pin_sub_category": "double",
    "python_runtime_types": verified_types,
    "repair_audit": str(REPAIR_AUDIT.relative_to(ROOT)).replace("\\", "/"),
}
BUILD_AUDIT.write_text(json.dumps(build_payload, indent=2), encoding="utf-8")

payload = {
    "$schema": "line-boss/audit/press-shop-pr004-surfaceforge-robot-numeric-state-repair-v020/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "UE_REAL_DOUBLE_STATE_TYPES_REPAIRED_AND_VERIFIED",
    "blueprint": BP_PATH,
    "map": MAP,
    "robot": ROBOT_LABEL,
    "default_types": default_types,
    "instance_types": verified_types,
    "instance_values": verified_values,
    "promotion_authorized": False,
}
REPAIR_AUDIT.parent.mkdir(parents=True, exist_ok=True)
REPAIR_AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR004_SURFACEFORGE_ROBOT_NUMERIC_STATE_V020_PASS audit={REPAIR_AUDIT}")
unreal.SystemLibrary.quit_editor()
