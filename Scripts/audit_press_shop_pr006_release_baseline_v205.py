"""Record the exact PR-006 visual/runtime baseline inherited by retained v205."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR005ReleaseArtCandidate_v205"
OUTPUT = (Path(unreal.Paths.project_saved_dir()) /
          "Audits/PressShopIntegration/press_shop_pr006_release_baseline_v205.json")

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")


def vec(value):
    return [round(float(value.x), 6), round(float(value.y), 6), round(float(value.z), 6)]


def rot(value):
    return [round(float(value.pitch), 6), round(float(value.yaw), 6), round(float(value.roll), 6)]


def actor_row(actor):
    root = actor.get_editor_property("root_component")
    row = {
        "label": actor.get_actor_label(),
        "class": actor.get_class().get_name(),
        "location_cm": vec(actor.get_actor_location()),
        "rotation_deg_pitch_yaw_roll": rot(actor.get_actor_rotation()),
        "scale": vec(actor.get_actor_scale3d()),
        "tags": sorted(str(tag) for tag in actor.tags),
        "collision_enabled": None,
    }
    if root and hasattr(root, "get_collision_enabled"):
        row["collision_enabled"] = str(root.get_collision_enabled())
    return row


all_actors = actors_api.get_all_level_actors()
pr006 = [actor_row(actor) for actor in all_actors
         if "PR006" in actor.get_actor_label().upper()]

nearby = []
for actor in all_actors:
    location = actor.get_actor_location()
    if -2150.0 <= location.x <= -1200.0 and -2500.0 <= location.y <= -1500.0:
        label = actor.get_actor_label()
        if "PR006" not in label.upper():
            nearby.append(actor_row(actor))

stations = [actor for actor in all_actors if isinstance(actor, unreal.LBPR006Station)]
expected = {}
for index in range(1, 10):
    expected[f"LB_PR006_V054_PR006_LowerRoll_{index:02d}"] = f"PR006_LowerRollMover_{index:02d}"
for index in range(1, 11):
    expected[f"LB_PR006_V054_PR006_UpperRoll_{index:02d}"] = f"PR006_UpperRollMover_{index:02d}"
expected.update({
    "LB_PR006_V054_PR006_UpperCassette_Operator": "PR006_UpperCassetteMover",
    "LB_PR006_V054_PR006_UpperCassette_Drive": "PR006_UpperCassetteMover",
})
for index, suffix in enumerate(("-1_-1", "-1_+1", "+1_-1", "+1_+1"), 1):
    expected[f"LB_PR006_V054_PR006_GapCylinder_{suffix}"] = f"PR006_GapCylinderMover_{index:02d}"
for index in range(1, 4):
    expected[f"LB_PR006_V054_PR006_DriveMotor_{index:02d}"] = f"PR006_DriveMotorMover_{index:02d}"

by_label = {actor.get_actor_label(): actor for actor in all_actors}
bindings = []
for label, expected_parent in expected.items():
    actor = by_label.get(label)
    root = actor.static_mesh_component if isinstance(actor, unreal.StaticMeshActor) else None
    parent = root.get_attach_parent() if root else None
    bindings.append({
        "actor": label,
        "expected_parent": expected_parent,
        "actual_parent": parent.get_name() if parent else None,
    })
binding_failures = [row for row in bindings if row["actual_parent"] != row["expected_parent"]]

payload = {
    "$schema": "cairnwell/audit/press-shop-pr006-release-baseline-v205/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": ("EXACT_V205_PR006_BASELINE_RECORDED__VISUAL_DERIVATIVE_REQUIRED__NOT_PROMOTED"
               if len(stations) == 1 else
               "V205_HAS_NO_PR006_NATIVE_AUTHORITY__INVALID_PR006_PARENT__NOT_PROMOTED"),
    "map": MAP,
    "pr006_actor_count": len(pr006),
    "pr006_authority_count": len(stations),
    "pr006_mover_binding_count": len(bindings),
    "pr006_mover_binding_failure_count": len(binding_failures),
    "pr006_mover_bindings": bindings,
    "pr006_actors": sorted(pr006, key=lambda row: row["label"]),
    "nearby_context": sorted(nearby, key=lambda row: row["label"]),
    "visual_findings_from_fixed_evidence": [
        "flat near-white floor overwhelms the machinery",
        "equipment reads as isolated islands inside an under-resolved hall",
        "process rollers and continuous strip lack enough material separation",
        "open service and hazard boundaries are weak at player height",
        "PR-006 fixed views are blockout-grade rather than release-quality",
    ],
    "invariants_for_successor": [
        "preserve the single native ALBPR006Station authority",
        "preserve all 28 exact mover bindings and local pivots",
        "do not move the approved PR-006 datum (-1700,-2000,0) cm",
        "do not stretch PR-006 or alter the resolved PR-006-to-Pro-PR-008 entry loop",
        "retain inherited PR-004 through PR-005 and PR-007 through PR-010 authorities",
    ],
}

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR006_V205_BASELINE_PASS actors={len(pr006)} bindings={len(bindings)} output={OUTPUT}")
unreal.SystemLibrary.quit_editor()
