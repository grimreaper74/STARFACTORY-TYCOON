"""Frame a close fixed camera on the PR-004 robot, tool and coil interface."""

import unreal


MAP = "/Game/LineBoss/Developer/Validation/PR004/LB_PR004_Inspection_Candidate_v009"
CAMERA = "LB_PR004_CAM_RobotTools"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

try:
    if not levels.load_level(MAP):
        raise RuntimeError(f"Could not load {MAP}")
    by_label = {actor.get_actor_label(): actor for actor in actors.get_all_level_actors()}
    camera = by_label.get(CAMERA)
    if camera is None:
        raise RuntimeError(f"Missing fixed camera {CAMERA}")
    start = unreal.Vector(-25.0, -690.0, 430.0)
    target = unreal.Vector(-155.0, 15.0, 175.0)
    camera.set_actor_location(start, False, False)
    camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(start, target), False)
    if not levels.save_current_level():
        raise RuntimeError("Failed to save PR-004 v009 robot evidence camera")
    unreal.log("LINE_BOSS_PR004_V009_ROBOT_EVIDENCE_CAMERA_PASS")
finally:
    unreal.SystemLibrary.quit_editor()
