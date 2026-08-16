"""Move the PR-004 tool rack to the side indicated by the robot wrist pose."""

import json
import math
from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir()).resolve()
MAP = "/Game/LineBoss/Developer/Validation/PR004/LB_PR004_Depackaging_Candidate_v007"
AUDIT = PROJECT / "Saved/Audits/pr004_tool_rack_pointing_pose_v007.json"

TARGETS = {
    # Rack front is at y~=341 cm; the current J6 wrist is at y=322 cm and
    # points +Y.  This makes the rack visually and mechanically face the wrist.
    "LB_PR004_robot_v002_tool_rack": ((-70.0, 390.0, 0.0), 0.0),
    "LB_PR004_robot_v002_band_tool": ((-205.0, 357.0, 108.0), 0.0),
    "LB_PR004_robot_v002_wrap_tool": ((-115.0, 357.0, 108.0), 0.0),
    "LB_PR004_robot_v002_edge_tool": ((-25.0, 357.0, 108.0), 0.0),
    "LB_PR004_robot_v002_inspection_tool": ((65.0, 357.0, 108.0), 0.0),
}
ROBOT_BASE = (-40.0, 70.0, 72.0)
MAX_TOOL_REACH_CM = 345.0

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

by_label = {actor.get_actor_label(): actor for actor in actors.get_all_level_actors()}
records = []
for label, (location, yaw) in TARGETS.items():
    actor = by_label.get(label)
    if actor is None:
        raise RuntimeError(f"Missing required actor {label}")
    actor.set_actor_location(unreal.Vector(*location), False, False)
    actor.set_actor_rotation(unreal.Rotator(0.0, 0.0, yaw), False)
    distance = None
    if label != "LB_PR004_robot_v002_tool_rack":
        distance = math.dist(ROBOT_BASE, location)
        if distance > MAX_TOOL_REACH_CM:
            raise RuntimeError(f"{label} exceeds tool-tip reach: {distance:.2f} cm")
    records.append({"actor": label, "location_cm": list(location), "yaw_deg": yaw, "pivot_distance_cm": distance})

# Fixed footprint check: rack x[-278,138], y[341,439] remains within the
# inner perimeter x[-570,570], y[-620,620].  Its closest face is 19 cm beyond
# the current J6 wrist y=322, matching the visible pointing direction.
if not levels.save_current_level():
    raise RuntimeError("Failed to save PR-004 tool-rack correction")

AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps({
    "$schema": "line-boss/audit/pr004-tool-rack-pointing-pose-v007/v1",
    "status": "CANDIDATE_STATIC_POINTING_POSE_PASS__ANIMATED_DOCKING_AND_SWEPT_COLLISION_REQUIRED",
    "map": MAP,
    "robot_base_cm": list(ROBOT_BASE),
    "current_j6_reference_cm": [-40.0, 322.0, 220.0],
    "current_j6_direction": "+Y toward rack",
    "rack_footprint_cm": [-278.0, 138.0, 341.0, 439.0],
    "maximum_tool_tip_reach_cm": MAX_TOOL_REACH_CM,
    "actors": records,
    "promotion_supported": False,
    "remaining_gates": [
        "authored tool-docking pose",
        "full J1-J6 swept collision",
        "rack maintenance aisle clearance",
        "fixed-camera visual comparison",
    ],
}, indent=2), encoding="utf-8")

unreal.log(f"LINE_BOSS_PR004_TOOL_RACK_POINTING_POSE_V007_PASS audit={AUDIT}")
unreal.SystemLibrary.quit_editor()
