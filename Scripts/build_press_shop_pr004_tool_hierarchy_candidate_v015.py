"""Bind the corrected PR-004 band tool to its changer and prove propagation."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PR004ToolAttachmentCandidate_v014"
DEST = "/Game/LineBoss/Maps/LB_PressShop_PR004ToolHierarchyCandidate_v015"
AUDIT = ROOT / "Saved/Audits/press_shop_pr004_tool_hierarchy_candidate_v015.json"
PREFIX = "LB_INT_PR004_V009_robot_v002_"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if unreal.EditorAssetLibrary.does_asset_exist(DEST):
    # A failed gate may have saved the v014-derived duplicate before rejecting
    # an attachment. Resume that generated candidate idempotently.
    if not levels.load_level(DEST):
        raise RuntimeError(f"Could not resume incomplete generated candidate {DEST}")
else:
    if not levels.new_level_from_template(DEST, BASE):
        raise RuntimeError(f"Could not create {DEST} from {BASE}")

by_label = {actor.get_actor_label(): actor for actor in actor_subsystem.get_all_level_actors()}
tool_label = PREFIX + "band_tool"
changer_label = PREFIX + "changer_body"
child_labels = [
    PREFIX + "band_left_capture",
    PREFIX + "band_right_capture",
    PREFIX + "band_cutter",
    PREFIX + "band_roll_left",
    PREFIX + "band_roll_right",
]
required = [tool_label, changer_label, *child_labels]
missing = [label for label in required if label not in by_label]
if missing:
    raise RuntimeError(f"Missing hierarchy actors: {missing}")

tool = by_label[tool_label]
changer = by_label[changer_label]


def parent_label(actor):
    parent = actor.get_attach_parent_actor()
    return parent.get_actor_label() if parent else None


before_parents = {label: parent_label(by_label[label]) for label in [tool_label, *child_labels]}
before_mobility = {}
for label in [tool_label, *child_labels]:
    component = by_label[label].static_mesh_component
    before_mobility[label] = str(component.get_editor_property("mobility"))
    component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
tool.attach_to_actor(
    changer, unreal.Name(""),
    unreal.AttachmentRule.KEEP_WORLD,
    unreal.AttachmentRule.KEEP_WORLD,
    unreal.AttachmentRule.KEEP_WORLD,
    False,
)
for label in child_labels:
    child = by_label[label]
    if child.get_attach_parent_actor() != tool:
        child.attach_to_actor(
            tool, unreal.Name(""),
            unreal.AttachmentRule.KEEP_WORLD,
            unreal.AttachmentRule.KEEP_WORLD,
            unreal.AttachmentRule.KEEP_WORLD,
            False,
        )

after_parents = {label: parent_label(by_label[label]) for label in [tool_label, *child_labels]}
after_mobility = {
    label: str(by_label[label].static_mesh_component.get_editor_property("mobility"))
    for label in [tool_label, *child_labels]
}
expected_parents = {tool_label: changer_label, **{label: tool_label for label in child_labels}}
if after_parents != expected_parents:
    raise RuntimeError(f"Hierarchy mismatch: {after_parents} != {expected_parents}")

# Exercise the hierarchy without persisting the displaced pose. Moving the
# changer must propagate an identical world delta through tool and sub-movers.
probe_delta = unreal.Vector(0.0, 30.0, 20.0)
probe_labels = [tool_label, *child_labels]
rest_changer = changer.get_actor_location()
rest_world = {label: by_label[label].get_actor_location() for label in probe_labels}
changer.set_actor_location(rest_changer + probe_delta, False, False)
probe_world = {label: by_label[label].get_actor_location() for label in probe_labels}
propagation = {}
for label in probe_labels:
    actual = probe_world[label] - rest_world[label]
    error = actual - probe_delta
    passed = abs(error.x) < 0.01 and abs(error.y) < 0.01 and abs(error.z) < 0.01
    propagation[label] = {
        "actual_delta_cm": [actual.x, actual.y, actual.z],
        "error_cm": [error.x, error.y, error.z],
        "pass": passed,
    }
    if not passed:
        raise RuntimeError(f"Attachment propagation failed for {label}: {propagation[label]}")
changer.set_actor_location(rest_changer, False, False)
for label in probe_labels:
    restored = by_label[label].get_actor_location()
    rest = rest_world[label]
    if abs(restored.x - rest.x) >= 0.01 or abs(restored.y - rest.y) >= 0.01 or abs(restored.z - rest.z) >= 0.01:
        raise RuntimeError(f"Failed to restore {label} after propagation probe")

if not levels.save_current_level():
    raise RuntimeError("Failed to save v015 hierarchy candidate")

payload = {
    "$schema": "line-boss/audit/press-shop-pr004-tool-hierarchy-candidate-v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "ATTACHMENT_HIERARCHY_AND_PROPAGATION_PASS__RUNTIME_INTERLOCK_AND_COLLISION_OPEN__NOT_PROMOTED",
    "base_map": BASE,
    "candidate_map": DEST,
    "before_parents": before_parents,
    "after_parents": after_parents,
    "expected_parents": expected_parents,
    "before_mobility": before_mobility,
    "after_mobility": after_mobility,
    "probe_delta_cm": [probe_delta.x, probe_delta.y, probe_delta.z],
    "propagation": propagation,
    "rest_pose_restored_before_save": True,
    "geometry_modified": False,
    "world_rest_transforms_modified": False,
    "tool_lock_presence_interlock_gate": "OPEN",
    "articulated_swept_collision_gate": "OPEN",
    "native_gameplay_runtime_gate": "BLOCKED_MISSING_WIN64_SDK_MSVC",
    "visual_gate": "PENDING_FRESH_FIXED_CAMERA_REVIEW",
    "promotion_authorized": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR004_TOOL_HIERARCHY_V015_PASS actors={len(probe_labels)} audit={AUDIT}")
unreal.SystemLibrary.quit_editor()
