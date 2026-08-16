"""Audit PR-004 robot wrist, changer, tools and tool child transforms in v006."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004LightingCandidate_v006"
OUT = ROOT / "Saved/Audits/press_shop_pr004_tool_attachment_source_v014.json"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

tokens = (
    "_j4", "_j5", "_j6", "tool_changer", "band_tool", "wrap_tool",
    "edge_tool", "inspection_tool", "band_left", "band_right", "band_cutter",
    "withdrawal", "vacuum", "peel", "edge_left", "edge_right", "bore", "shutter",
)
rows = []
for actor in actors.get_all_level_actors():
    label = actor.get_actor_label().lower()
    if not label.startswith("lb_int_pr004_v009_robot_v002_"):
        continue
    if not any(token in label for token in tokens):
        continue
    loc = actor.get_actor_location()
    rot = actor.get_actor_rotation()
    rows.append({
        "actor": actor.get_actor_label(),
        "location_cm": [loc.x, loc.y, loc.z],
        "rotation_deg": [rot.roll, rot.pitch, rot.yaw],
        "class": actor.get_class().get_name(),
    })

payload = {
    "$schema": "line-boss/audit/press-shop-pr004-tool-attachment-source-v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "map": MAP,
    "actors": sorted(rows, key=lambda row: row["actor"]),
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR004_TOOL_ATTACHMENT_SOURCE_V014_PASS actors={len(rows)} audit={OUT}")
unreal.SystemLibrary.quit_editor()
