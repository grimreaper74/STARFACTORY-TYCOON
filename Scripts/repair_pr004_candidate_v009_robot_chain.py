"""Reassemble the PR-004 v009 robot around one compact local kinematic datum."""

import json
from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir()).resolve()
MAP = "/Game/LineBoss/Developer/Validation/PR004/LB_PR004_Inspection_Candidate_v009"
OUT = PROJECT / "Saved/Audits/pr004_v009_robot_chain_repair.json"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def set_pose(actor, xyz, rot=(0.0, 0.0, 90.0)):
    actor.set_actor_location(unreal.Vector(*xyz), False, False)
    actor.set_actor_rotation(unreal.Rotator(*rot), False)


try:
    if not levels.load_level(MAP):
        raise RuntimeError(f"Could not load {MAP}")
    by_label = {a.get_actor_label(): a for a in actors.get_all_level_actors()}

    # These imported meshes arrived with independent object origins.  Treat the
    # authored visual pieces as one rigid validation pose around the robot base.
    # The robot remains unscaled and every future animation pivot stays explicit.
    poses = {
        "LB_PR004_robot_v002_base": ((70.0, 35.0, 0.0), (0.0, 0.0, 180.0)),
        "LB_PR004_robot_v002_j1": ((70.0, 35.0, 72.0), (0.0, 0.0, 180.0)),
        "LB_PR004_robot_v002_j2": ((58.0, 35.0, 136.0), (0.0, 0.0, 180.0)),
        "LB_PR004_robot_v002_j3": ((-12.0, 35.0, 220.0), (0.0, 0.0, 180.0)),
        "LB_PR004_robot_v002_j4": ((-125.0, 35.0, 220.0), (0.0, 0.0, 180.0)),
        "LB_PR004_robot_v002_j5": ((-155.0, 35.0, 220.0), (0.0, 0.0, 180.0)),
        "LB_PR004_robot_v002_j6": ((-182.0, 35.0, 220.0), (0.0, 0.0, 180.0)),
        "LB_PR004_robot_v002_changer_body": ((-204.0, 35.0, 220.0), (0.0, 0.0, 180.0)),
        "LB_PR004_robot_v002_changer_lock": ((-204.0, 35.0, 220.0), (0.0, 0.0, 180.0)),
        "LB_PR004_robot_v002_dress_lower": ((68.0, 35.0, 74.0), (0.0, 0.0, 180.0)),
        "LB_PR004_robot_v002_dress_upper": ((58.0, 35.0, 136.0), (0.0, 0.0, 180.0)),
        "LB_PR004_robot_v002_dress_wrist": ((-125.0, 35.0, 220.0), (0.0, 0.0, 180.0)),
    }

    moved = []
    missing = []
    for label, (xyz, rot) in poses.items():
        actor = by_label.get(label)
        if actor is None:
            missing.append(label)
            continue
        set_pose(actor, xyz, rot)
        moved.append(label)

    if missing:
        raise RuntimeError(f"Missing robot actors: {missing}")
    if not levels.save_current_level():
        raise RuntimeError("Failed to save PR-004 v009 robot-chain repair")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "$schema": "line-boss/audit/pr004-v009-robot-chain-repair/v1",
        "map": MAP,
        "status": "ROBOT_CHAIN_REASSEMBLY_PASS__VISUAL_REVIEW_REQUIRED",
        "robot_base_cm": [70.0, 35.0, 0.0],
        "coil_cradle_centre_cm": [-310.0, 0.0, 0.0],
        "unscaled": True,
        "moved": moved,
        "promotion_supported": False,
    }, indent=2), encoding="utf-8")
    unreal.log(f"LINE_BOSS_PR004_V009_ROBOT_CHAIN_REPAIR_PASS moved={len(moved)} audit={OUT}")
finally:
    unreal.SystemLibrary.quit_editor()
