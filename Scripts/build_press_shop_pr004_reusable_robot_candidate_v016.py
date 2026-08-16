"""Replace the v014 map-only robot chain with one reusable Blueprint instance."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PR004ToolAttachmentCandidate_v014"
DEST = "/Game/LineBoss/Maps/LB_PressShop_PR004ReusableRobotPlateCandidate_v019"
BP_PATH = "/Game/LineBoss/Equipment/Robots/Modular6Axis/Candidate_v005/BP_LB_Modular6AxisRobot_400kg_v005"
AUDIT = ROOT / "Saved/Audits/press_shop_pr004_reusable_robot_plate_candidate_v019.json"
PREFIX = "LB_INT_PR004_V009_robot_v002_"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
lib = unreal.EditorAssetLibrary
bp_lib = unreal.BlueprintEditorLibrary
if lib.does_asset_exist(DEST):
    if not levels.load_level(DEST):
        raise RuntimeError(f"Could not load generated candidate {DEST}")
else:
    if not levels.new_level_from_template(DEST, BASE):
        raise RuntimeError(f"Could not create {DEST} from {BASE}")

by_label = {actor.get_actor_label(): actor for actor in actor_subsystem.get_all_level_actors()}
module_ids = [
    "base", "j1", "j2", "j3", "j4", "j5", "j6", "changer_body", "changer_lock",
    "dress_lower", "dress_upper", "dress_wrist", "band_tool", "band_left_capture",
    "band_right_capture", "band_cutter", "band_roll_left", "band_roll_right",
]
labels = [PREFIX + module_id for module_id in module_ids]
base_actor = by_label.get(PREFIX + "base")
existing_bp = [a for a in actor_subsystem.get_all_level_actors() if a.get_actor_label() == "LB_INT_PR004_BP_ModularRobot_400kg_v005"]
if base_actor is not None:
    base_location = base_actor.get_actor_location()
    base_rotation = base_actor.get_actor_rotation()
    removable = [by_label[label] for label in labels if label in by_label]
    # Destroy explicit children before their parents to avoid attachment-order ambiguity.
    for actor in reversed(removable):
        actor_subsystem.destroy_actor(actor)
elif existing_bp:
    base_location = existing_bp[0].get_actor_location()
    base_rotation = existing_bp[0].get_actor_rotation()
else:
    raise RuntimeError("Neither source robot base nor an idempotent reusable instance exists")

for actor in existing_bp:
    actor_subsystem.destroy_actor(actor)
bp = lib.load_asset(BP_PATH)
if bp is None:
    raise RuntimeError(f"Missing reusable robot Blueprint {BP_PATH}")
robot = actor_subsystem.spawn_actor_from_class(bp_lib.generated_class(bp), base_location, base_rotation)
robot.set_actor_label("LB_INT_PR004_BP_ModularRobot_400kg_v005")
robot.set_editor_property("tags", [
    unreal.Name("LB.Asset.CandidateNotPromoted"), unreal.Name("LB.Equipment.Robot.Modular6Axis"),
    unreal.Name("LB.Station.PR004"), unreal.Name("LB.Tool.BandCutterCapture"),
])
instance_state = {
    "StationId": "PR-004",
    "EquipmentId": "PR004-RBT-01",
    "ConditionAgeYears": 7.0,
    "ConditionSeed": 4001,
    "CurrentToolId": "BandCutterCapture",
    "J1Degrees": 0.0,
    "J2Degrees": 0.0,
    "J3Degrees": 0.0,
    "J4Degrees": 0.0,
    "J5Degrees": 0.0,
    "J6Degrees": 0.0,
    "Enabled": False,
    "ToolLocked": True,
    "FaultCode": "RESTORATION_REQUIRED",
    "OperatingHours": 18420.0,
    "ServiceCycles": 318500,
}
for property_name, value in instance_state.items():
    robot.set_editor_property(property_name, value)
verified_state = {name: robot.get_editor_property(name) for name in instance_state}
if verified_state != instance_state:
    raise RuntimeError(f"Reusable robot instance-state mismatch: {verified_state}")
branding_components = []
plate_material = lib.load_asset("/Game/LineBoss/Brand/Cairnwell/Candidate_v005/RobotPlate/M_Cairnwell_PR004_RobotPlate_v001")
if plate_material is None:
    raise RuntimeError("Missing deterministic PR-004 robot plate material")
for component in robot.get_components_by_class(unreal.StaticMeshComponent):
    component_name = component.get_name()
    if "RobotAssetPlateFace" in component_name:
        component.set_material(0, plate_material)
        branding_components.append({
            "component": component_name,
            "material": plate_material.get_path_name(),
            "equipment_id": instance_state["EquipmentId"],
        })
if len(branding_components) != 1:
    raise RuntimeError(f"Expected one replaceable robot plate face; found {branding_components}")

remaining_old = [a.get_actor_label() for a in actor_subsystem.get_all_level_actors() if a.get_actor_label() in labels]
if remaining_old:
    raise RuntimeError(f"Old robot-chain actors remain: {remaining_old}")
if not levels.save_current_level():
    raise RuntimeError("Could not save reusable robot v016 candidate")

components = robot.get_components_by_class(unreal.ActorComponent)
payload = {
    "$schema": "line-boss/audit/press-shop-pr004-reusable-robot-candidate-v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "REUSABLE_ROBOT_DETERMINISTIC_PLATE_AND_STATE_INTEGRATED__FRESH_VISUAL_AND_RUNTIME_GATES_REQUIRED__NOT_PROMOTED",
    "base_map": BASE,
    "candidate_map": DEST,
    "robot_blueprint": BP_PATH,
    "robot_actor": robot.get_actor_label(),
    "robot_world_location_cm": [base_location.x, base_location.y, base_location.z],
    "robot_world_rotation_deg": [base_rotation.roll, base_rotation.pitch, base_rotation.yaw],
    "replaced_map_actor_count": len(labels),
    "blueprint_component_count": len(components),
    "instance_state": verified_state,
    "branding_components": branding_components,
    "cairnwell_internal_project_use_gate": "CLEARED_BY_USER_CONFIRMATION",
    "old_robot_actor_labels_remaining": remaining_old,
    "rack_and_unselected_tool_actors_preserved": True,
    "geometry_modified": False,
    "visual_gate": "PENDING_FRESH_FIXED_CAMERA_REVIEW",
    "runtime_animation_interlock_save_gate": "OPEN",
    "collision_gate": "OPEN_COMPLEX_AS_SIMPLE",
    "promotion_authorized": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR004_REUSABLE_ROBOT_V016_PASS components={len(components)} audit={AUDIT}")
unreal.SystemLibrary.quit_editor()
