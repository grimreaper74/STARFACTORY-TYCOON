"""Mount the PR-004 band cutter/capture tool for a deterministic clearance pose.

The four rack tools remain independent modular assets.  This script moves only
the band-tool assembly from its rack datum to the robot quick-changer, preserving
the authored child offsets.  The pose is evidence-only and is not a promotion.
"""

import json
from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir()).resolve()
MAP = "/Game/LineBoss/Developer/Validation/PR004/LB_PR004_Inspection_Candidate_v009"
OUT = PROJECT / "Saved/Audits/pr004_v009_band_tool_pose.json"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


try:
    if not levels.load_level(MAP):
        raise RuntimeError(f"Could not load {MAP}")
    by_label = {actor.get_actor_label(): actor for actor in actors.get_all_level_actors()}

    # The tool was authored on the rack with its +X process axis.  Rotate it
    # 180 degrees so the process axis follows the robot's west-facing wrist.
    # Keep 35 cm between the changer datum and tool body datum so the cutter
    # face remains visibly outside the coil face in this validation pose.
    tool_datum = unreal.Vector(-239.0, 35.0, 220.0)
    yaw = unreal.Rotator(0.0, 0.0, 180.0)

    # Explicit UE working-pose offsets make the operation idempotent.  The FBX
    # manifest's parent-relative figures describe the original rack/preview
    # layout and put the independent movers through the coil when mirrored into
    # this cell.  These values retain separate animation pivots while gathering
    # the jaws, cutter and rolls around the actual tool nose.
    offsets = {
        "LB_PR004_robot_v002_band_tool": (0.0, 0.0, 0.0),
        "LB_PR004_robot_v002_band_left_capture": (45.0, -28.0, 0.0),
        "LB_PR004_robot_v002_band_right_capture": (45.0, 28.0, 0.0),
        "LB_PR004_robot_v002_band_cutter": (60.0, 0.0, 0.0),
        "LB_PR004_robot_v002_band_roll_left": (45.0, -28.0, -15.0),
        "LB_PR004_robot_v002_band_roll_right": (45.0, 28.0, -15.0),
    }
    labels = list(offsets)
    missing = [label for label in labels if label not in by_label]
    if missing:
        raise RuntimeError(f"Missing band-tool actors: {missing}")

    moved = []
    for label in labels:
        actor = by_label[label]
        relative = unreal.Vector(*offsets[label])
        rotated = unreal.Vector(-relative.x, -relative.y, relative.z)
        actor.set_actor_location(tool_datum + rotated, False, False)
        actor.set_actor_rotation(yaw, False)
        moved.append(label)

    if not levels.save_current_level():
        raise RuntimeError("Failed to save PR-004 v009 band-tool pose")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "$schema": "line-boss/audit/pr004-v009-band-tool-pose/v1",
        "map": MAP,
        "status": "BAND_TOOL_MOUNTED__VISUAL_REVIEW_REQUIRED",
        "robot_changer_datum_cm": [-204.0, 35.0, 220.0],
        "tool_datum_cm": [-239.0, 35.0, 220.0],
        "tool_yaw_deg": 180.0,
        "moved": moved,
        "promotion_supported": False,
    }, indent=2), encoding="utf-8")
    unreal.log(f"LINE_BOSS_PR004_V009_BAND_TOOL_POSE_PASS moved={len(moved)} audit={OUT}")
finally:
    unreal.SystemLibrary.quit_editor()
