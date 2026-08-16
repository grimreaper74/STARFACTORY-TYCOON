"""Remove the artificial PR-004 band-tool/changer gap in a v006-derived candidate."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PR004LightingCandidate_v006"
DEST = "/Game/LineBoss/Maps/LB_PressShop_PR004ToolAttachmentCandidate_v014"
AUDIT = ROOT / "Saved/Audits/press_shop_pr004_tool_attachment_candidate_v014.json"
PREFIX = "LB_INT_PR004_V009_robot_v002_"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.new_level_from_template(DEST, BASE):
    raise RuntimeError(f"Could not create {DEST} from {BASE}")

by_label = {actor.get_actor_label(): actor for actor in actors.get_all_level_actors()}
labels = [
    PREFIX + "band_tool",
    PREFIX + "band_left_capture",
    PREFIX + "band_right_capture",
    PREFIX + "band_cutter",
    PREFIX + "band_roll_left",
    PREFIX + "band_roll_right",
]
missing = [label for label in labels if label not in by_label]
if missing:
    raise RuntimeError(f"Missing band-tool assembly actors: {missing}")

j6 = by_label[PREFIX + "j6"]
changer = by_label[PREFIX + "changer_body"]
tool = by_label[PREFIX + "band_tool"]
before_tool = tool.get_actor_location()
changer_datum = changer.get_actor_location()
delta = changer_datum - before_tool

# The previous evidence pose inserted a 35 cm datum separation. All six actors
# are independent modular movers, so translate the complete tool assembly by the
# same vector and preserve rotations and child offsets exactly.
before = {}
after = {}
for label in labels:
    actor = by_label[label]
    loc = actor.get_actor_location()
    before[label] = [loc.x, loc.y, loc.z]
    actor.set_actor_location(loc + delta, False, False)
    new_loc = actor.get_actor_location()
    after[label] = [new_loc.x, new_loc.y, new_loc.z]

camera_label = "LB_AUDIT_PR004_ToolAttachment_Close_v014"
camera = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(-5590.0, -1540.0, 395.0))
camera.set_actor_label(camera_label)
camera.set_actor_rotation(
    unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(), changer_datum), False
)
camera.camera_component.set_editor_property("field_of_view", 38.0)

if not levels.save_current_level():
    raise RuntimeError("Failed to save v014 tool-attachment candidate")

payload = {
    "$schema": "line-boss/audit/press-shop-pr004-tool-attachment-candidate-v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "TOOL_ATTACHMENT_CANDIDATE__FRESH_VISUAL_REVIEW_REQUIRED__NOT_PROMOTED",
    "base_map": BASE,
    "candidate_map": DEST,
    "source_defect": "Earlier validation pose intentionally separated changer and band-tool datums by 35 cm.",
    "j6_datum_cm": [j6.get_actor_location().x, j6.get_actor_location().y, j6.get_actor_location().z],
    "changer_datum_cm": [changer_datum.x, changer_datum.y, changer_datum.z],
    "tool_datum_before_cm": [before_tool.x, before_tool.y, before_tool.z],
    "assembly_translation_cm": [delta.x, delta.y, delta.z],
    "tool_datum_after_cm": after[PREFIX + "band_tool"],
    "moved_actors": labels,
    "before": before,
    "after": after,
    "geometry_modified": False,
    "non_tool_transforms_modified": False,
    "camera": camera_label,
    "runtime_parenting_gate": "OPEN_INDEPENDENT_STATIC_MESH_ACTORS_REQUIRE_RUNTIME_ATTACHMENT_HIERARCHY",
    "swept_collision_gate": "OPEN",
    "visual_gate": "PENDING_FRESH_FIXED_CAMERA_REVIEW",
    "promotion_authorized": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR004_TOOL_ATTACHMENT_V014_PASS moved={len(labels)} delta={delta} audit={AUDIT}")
unreal.SystemLibrary.quit_editor()
