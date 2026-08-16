"""Reframe PR-004 v008 fixed evidence cameras for the authoritative 22 x 12 m cell."""

import unreal


MAP = "/Game/LineBoss/Developer/Validation/PR004/LB_PR004_Inspection_Candidate_v008"
CAMERAS = {
    "LB_PR004_CAM_Overview_SW": ((-1850, -1550, 1250), (0, 0, 100)),
    "LB_PR004_CAM_Overview_NE": ((1750, 1450, 1150), (0, 0, 100)),
    "LB_PR004_CAM_Top": ((0, 0, 2850), (0, 0, 0)),
    "LB_PR004_CAM_CradleClose": ((-1380, -430, 500), (-680, 0, 105)),
    "LB_PR004_CAM_RobotTools": ((720, 40, 560), (0, 390, 115)),
    "LB_PR004_CAM_PackagingClose": ((-1350, 380, 430), (-680, 0, 110)),
    "LB_PR004_CAM_FilmDewrap": ((1480, -460, 520), (650, 0, 110)),
}

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

try:
    if not levels.load_level(MAP):
        raise RuntimeError(f"Could not load {MAP}")
    by_label = {actor.get_actor_label(): actor for actor in actors.get_all_level_actors()}
    for label, (location, target) in CAMERAS.items():
        camera = by_label.get(label)
        if camera is None:
            raise RuntimeError(f"Missing fixed camera {label}")
        start = unreal.Vector(*location)
        camera.set_actor_location(start, False, False)
        camera.set_actor_rotation(
            unreal.MathLibrary.find_look_at_rotation(start, unreal.Vector(*target)),
            False,
        )
    if not levels.save_current_level():
        raise RuntimeError("Failed to save PR-004 v008 camera framing")
    unreal.log(f"LINE_BOSS_PR004_V008_CAMERAS_PASS count={len(CAMERAS)}")
finally:
    unreal.SystemLibrary.quit_editor()
