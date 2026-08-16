"""Align the compact PR-004 stand to its existing crane/datum centre."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004PackagingPolishCandidate_v026"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr004_datum_alignment_v026.json"
SHIFT_X_CM = 310.0
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")


def belongs_to_moving_cluster(label):
    return (
        label == "LB_INT_PR004_V024_InteractiveUnpackageStation"
        or label == "LB_INT_PR004_V009_DRESS08_EStop_Operator"
        or label.startswith("LB_INT_PR004_V009_DRESS08_FaceInspectionMast_")
        or label.startswith("LB_INT_PR004_V009_powered_cradle_v001_")
        or label.startswith("LB_PR004_V025_")
        or label == "LB_PR004_V026_FloorStencil"
        or label.startswith("LB_PR004_V026_HMI_")
    )


moved = []
for actor in actors.get_all_level_actors():
    label = actor.get_actor_label()
    if not belongs_to_moving_cluster(label):
        continue
    before = actor.get_actor_location()
    after = unreal.Vector(before.x + SHIFT_X_CM, before.y, before.z)
    actor.set_actor_location(after, False, False)
    moved.append({"actor": label, "before_cm": [before.x, before.y, before.z],
                  "after_cm": [after.x, after.y, after.z]})

expected_labels = {
    "LB_INT_PR004_V024_InteractiveUnpackageStation",
    "LB_INT_PR004_V009_DRESS08_EStop_Operator",
    "LB_INT_PR004_V009_DRESS08_FaceInspectionMast_N",
    "LB_INT_PR004_V009_DRESS08_FaceInspectionMast_S",
    "LB_INT_PR004_V009_powered_cradle_v001_end_stop_locator",
    "LB_INT_PR004_V009_powered_cradle_v001_index_drive",
    "LB_INT_PR004_V009_powered_cradle_v001_left_side_clamp",
    "LB_INT_PR004_V009_powered_cradle_v001_right_side_clamp",
    "LB_INT_PR004_V009_powered_cradle_v001_static",
    "LB_PR004_V026_FloorStencil",
    "LB_PR004_V026_HMI_Base",
    "LB_PR004_V026_HMI_Post",
    "LB_PR004_V026_HMI_Bezel",
}
moved_labels = {row["actor"] for row in moved}
missing = sorted(expected_labels - moved_labels)
floor_mark_count = sum(1 for label in moved_labels if label.startswith("LB_PR004_V025_"))
if missing or floor_mark_count != 11:
    raise RuntimeError(f"Refusing incomplete PR-004 alignment missing={missing} floor_marks={floor_mark_count}")

by_label = {actor.get_actor_label(): actor for actor in actors.get_all_level_actors()}
station = by_label["LB_INT_PR004_V024_InteractiveUnpackageStation"]
cradle = by_label["LB_INT_PR004_V009_powered_cradle_v001_static"]
datum = by_label["LB_INT_PR004_V009_Datum"]
hook = by_label["LB_INT_FRONT_40T_CHook"]
alignment_x = [station.get_actor_location().x, cradle.get_actor_location().x,
               datum.get_actor_location().x, hook.get_actor_location().x]
if max(alignment_x) - min(alignment_x) > 0.01:
    raise RuntimeError(f"PR-004/crane datum alignment failed: {alignment_x}")

if not levels.save_current_level():
    raise RuntimeError("Could not save datum-aligned v026 map")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "$schema": "line-boss/audit/press-shop-pr004-datum-alignment-v026/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "COMPACT_STAND_ALIGNED_TO_EXISTING_PR004_CRANE_DATUM__VISUAL_AND_CLEARANCE_REGATE_OPEN__NOT_PROMOTED",
    "map": MAP,
    "reason": "Remove the preparation footprint from the inherited dark PR-003 floor strip without repainting the main route",
    "shift_x_cm": SHIFT_X_CM,
    "alignment_x_cm": alignment_x,
    "moved_actor_count": len(moved),
    "moved_actors": moved,
    "fixed_authorities_preserved": ["LB_INT_PR004_V009_Datum", "LB_INT_FRONT_40T_CHook",
                                     "LB_MOTH_V004_EmergencyPool_02", "LB_PRESS_V023_PR004_Reflection"],
    "accepted_v006_untouched": True,
    "promotion_authorized": False,
}, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR004_DATUM_ALIGNMENT_V026_PASS moved={len(moved)} x={alignment_x[0]}")
unreal.SystemLibrary.quit_editor()
