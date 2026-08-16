"""Fresh-process spawned-instance movement and collision audit for CR01 v057."""

from datetime import datetime, timezone
import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BP_PATH = "/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v057/Blueprints/BP_LB_CR01_CleaningAMR_v057"
OUT = ROOT / "Saved/Audits/lb_cr01_candidate_v057_movement_independent.json"

assets = unreal.EditorAssetLibrary
blueprints = unreal.BlueprintEditorLibrary
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def normalize(value):
    name = str(value)
    for suffix in ("_GEN_VARIABLE", "_0"):
        if name.endswith(suffix):
            name = name[:-len(suffix)]
    return name


failures = []
blueprint = assets.load_asset(BP_PATH)
if not isinstance(blueprint, unreal.Blueprint):
    raise RuntimeError(f"Missing CR01 v057 Blueprint: {BP_PATH}")
blueprints.compile_blueprint(blueprint)
blueprint_status = str(blueprint.get_editor_property("status"))
if "ERROR" in blueprint_status.upper():
    failures.append(f"Blueprint status is {blueprint_status}")

generated_class = blueprints.generated_class(blueprint)
robot = actors.spawn_actor_from_class(generated_class, unreal.Vector(0.0, 0.0, 150.0), unreal.Rotator())
if robot is None:
    raise RuntimeError("Could not spawn disposable CR01 v057 audit instance")
robot.set_actor_label("LB_CR01_v057_DisposableMovementAudit")

all_components = robot.get_components_by_class(unreal.ActorComponent)
components = {normalize(component.get_name()): component for component in all_components}
movements = robot.get_components_by_class(unreal.FloatingPawnMovement)
if len(movements) != 1:
    failures.append(f"Expected one FloatingPawnMovement, found {len(movements)}")
    movement = None
else:
    movement = movements[0]

movement_row = None
if movement is not None:
    updated = movement.get_editor_property("updated_component")
    updated_name = normalize(updated.get_name()) if updated else None
    updated_owner = updated.get_owner() if updated else None
    movement_owner = movement.get_owner()
    movement_row = {
        "component": normalize(movement.get_name()),
        "owner_is_spawned_robot": movement_owner == robot,
        "updated_component": updated_name,
        "updated_component_owner_is_spawned_robot": updated_owner == robot,
        "max_speed_cm_s": float(movement.get_editor_property("max_speed")),
        "acceleration_cm_s2": float(movement.get_editor_property("acceleration")),
        "deceleration_cm_s2": float(movement.get_editor_property("deceleration")),
        "turning_boost": float(movement.get_editor_property("turning_boost")),
    }
    if movement_owner != robot:
        failures.append("Movement component is not owned by spawned robot")
    if updated_name != "Collision_CR01_Base" or updated_owner != robot:
        failures.append(
            f"Updated component did not remap to spawned robot Collision_CR01_Base: "
            f"name={updated_name} owner_matches={updated_owner == robot}"
        )
    for key, expected in (
        ("max_speed_cm_s", 120.0),
        ("acceleration_cm_s2", 80.0),
        ("deceleration_cm_s2", 120.0),
        ("turning_boost", 4.0),
    ):
        if abs(movement_row[key] - expected) > 0.001:
            failures.append(f"Movement setting mismatch {key}: {movement_row[key]} != {expected}")

blocking_names = ["Collision_CR01_Base", "Collision_CR01_Upper", "Collision_CR01_Roof"]
query_names = [
    "Query_CR01_FrontBrush", "Query_CR01_SideBrush_L", "Query_CR01_SideBrush_R",
    "Query_CR01_ScrubDeck", "Query_CR01_Squeegee",
]
collision_rows = []
for name in blocking_names + query_names:
    component = components.get(name)
    if not isinstance(component, unreal.PrimitiveComponent):
        failures.append(f"Missing collision/query component {name}")
        continue
    profile = str(component.get_collision_profile_name())
    generates_overlap = bool(component.get_editor_property("generate_overlap_events"))
    collision_rows.append({
        "component": name,
        "owner_is_spawned_robot": component.get_owner() == robot,
        "collision_profile": profile,
        "generate_overlap_events": generates_overlap,
    })
    if component.get_owner() != robot:
        failures.append(f"{name} is not owned by spawned robot")
    if name in blocking_names and profile != "BlockAllDynamic":
        failures.append(f"{name} blocking profile is {profile}")
    if name in query_names and (profile != "OverlapAllDynamic" or not generates_overlap):
        failures.append(f"{name} query settings are profile={profile} overlap={generates_overlap}")

result = {
    "$schema": "line-boss/audit/lb-cr01-candidate-v057-movement-independent",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "FRESH_SPAWN_MOVEMENT_OWNERSHIP_AND_COLLISION_PASS__NAV_RUNTIME_GATE_OPEN__NOT_PROMOTED" if not failures else "FRESH_SPAWN_MOVEMENT_OWNERSHIP_OR_COLLISION_FAIL__NOT_PROMOTED",
    "blueprint": BP_PATH,
    "blueprint_status": blueprint_status,
    "spawned_class_is_pawn": isinstance(robot, unreal.Pawn),
    "movement": movement_row,
    "blocking_collision_component_count": sum(1 for row in collision_rows if row["component"] in blocking_names),
    "cleaning_query_component_count": sum(1 for row in collision_rows if row["component"] in query_names),
    "collision_components": collision_rows,
    "deep_fault_system_required": False,
    "runtime_navigation_gate_passed": False,
    "failures": failures,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
actors.destroy_actor(robot)
if failures:
    unreal.log_error(f"LINE_BOSS_CR01_V057_MOVEMENT_AUDIT_FAIL failures={len(failures)} audit={OUT}")
    raise RuntimeError("; ".join(failures))
unreal.log(f"LINE_BOSS_CR01_V057_MOVEMENT_AUDIT_PASS audit={OUT}")
