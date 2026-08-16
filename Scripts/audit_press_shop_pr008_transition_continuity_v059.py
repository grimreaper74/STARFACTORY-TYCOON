"""Verify both joints of the v059 PR-006-to-PR-008 transition in actual Unreal bounds."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR008TransitionGuardCandidate_v059"
AUDIT = ROOT / "Saved/Audits/press_shop_pr008_transition_continuity_v059.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

labels = {
    "pr006": "LB_PR006_V054_PR006_ThreadedStrip",
    "transition": "LB_PR008_V059_PR008_TransitionStrip",
    "pr008": "LB_PR008_V058_PR008_ThreadedStrip",
}
found = {actor.get_actor_label(): actor for actor in actors.get_all_level_actors()}
if not all(label in found for label in labels.values()):
    raise RuntimeError(f"Missing transition contract actor; required={labels}")


def bounds(actor):
    origin, extent = actor.get_actor_bounds(False, False)
    return {
        "actor": actor.get_actor_label(),
        "origin_cm": [origin.x, origin.y, origin.z],
        "extent_cm": [extent.x, extent.y, extent.z],
        "min_cm": [origin.x - extent.x, origin.y - extent.y, origin.z - extent.z],
        "max_cm": [origin.x + extent.x, origin.y + extent.y, origin.z + extent.z],
    }


b = {key: bounds(found[label]) for key, label in labels.items()}
upstream_gap_cm = b["transition"]["min_cm"][0] - b["pr006"]["max_cm"][0]
downstream_gap_cm = b["pr008"]["min_cm"][0] - b["transition"]["max_cm"][0]
lateral_delta_cm = max(
    abs(b["transition"]["origin_cm"][1] - b["pr006"]["origin_cm"][1]),
    abs(b["pr008"]["origin_cm"][1] - b["transition"]["origin_cm"][1]),
)
continuous = upstream_gap_cm <= 1.0 and downstream_gap_cm <= 1.0 and lateral_delta_cm <= 1.0

payload = {
    "$schema": "line-boss/audit/press-shop-pr008-transition-continuity-v059/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": (
        "PR006_PR008_TRANSITION_CONTINUITY_PASS__NOT_PROMOTED"
        if continuous
        else "PR006_PR008_TRANSITION_CONTINUITY_FAIL__NOT_PROMOTED"
    ),
    "map": MAP,
    "bounds": b,
    "upstream_joint_gap_cm": upstream_gap_cm,
    "downstream_joint_gap_cm": downstream_gap_cm,
    "maximum_lateral_centre_delta_cm": lateral_delta_cm,
    "maximum_allowed_joint_gap_cm": 1.0,
    "continuous": continuous,
    "promotion_authorized": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(
    "LINE_BOSS_PR008_V059_CONTINUITY "
    f"upstream_gap_cm={upstream_gap_cm:.4f} downstream_gap_cm={downstream_gap_cm:.4f} "
    f"lateral_delta_cm={lateral_delta_cm:.4f} continuous={continuous}"
)
unreal.SystemLibrary.quit_editor()
