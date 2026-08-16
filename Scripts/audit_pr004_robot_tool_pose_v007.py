"""Record PR-004 robot wrist, rack and tool actor transforms for layout repair."""

import json
from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir()).resolve()
MAP = "/Game/LineBoss/Developer/Validation/PR004/LB_PR004_Depackaging_Candidate_v007"
AUDIT = PROJECT / "Saved/Audits/pr004_robot_tool_pose_v007.json"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

tokens = ("_base", "_j1", "_j4", "_j5", "_j6", "tool_changer", "tool_rack", "_band_tool", "_wrap_tool", "_edge_tool", "_inspection_tool")
records = []
for actor in actors.get_all_level_actors():
    label = actor.get_actor_label()
    if not label.startswith("LB_PR004_robot_v002_") or not any(token in label for token in tokens):
        continue
    location = actor.get_actor_location()
    rotation = actor.get_actor_rotation()
    records.append({
        "actor": label,
        "location_cm": [location.x, location.y, location.z],
        "rotation_deg": [rotation.roll, rotation.pitch, rotation.yaw],
    })

AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps({"map": MAP, "actors": sorted(records, key=lambda r: r["actor"])}, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR004_ROBOT_TOOL_POSE_V007_PASS actors={len(records)} audit={AUDIT}")
unreal.SystemLibrary.quit_editor()
