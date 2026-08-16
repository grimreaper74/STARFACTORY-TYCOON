"""Render the shared-HMI fixed camera without opening the Unreal editor UI."""

from __future__ import annotations

from pathlib import Path

import unreal


MAP_PATH = "/Game/LineBoss/Developer/Validation/LB_HMI_Validation"
CAMERA_LABEL = "LB_CAM_HMI_FrontValidation"
OUTPUT = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/HMI/shared_hmi_unreal_front_v002.png"


levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels.load_level(MAP_PATH)
camera = next((actor for actor in actors.get_all_level_actors() if actor.get_actor_label() == CAMERA_LABEL), None)
if camera is None:
    raise RuntimeError(f"Camera {CAMERA_LABEL} was not found in {MAP_PATH}")

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
unreal.AutomationLibrary.finish_loading_before_screenshot()
task = unreal.AutomationLibrary.take_high_res_screenshot(
    1920,
    1080,
    str(OUTPUT),
    camera=camera,
    mask_enabled=False,
    capture_hdr=False,
    comparison_tolerance=unreal.ComparisonTolerance.LOW,
    comparison_notes="Line Boss shared HMI fixed-camera Unreal validation",
    delay=0.0,
    force_game_view=True,
)
if not task.is_valid_task():
    raise RuntimeError("Unreal did not create a valid screenshot task")
unreal.log(f"LINE_BOSS_HMI_SCREENSHOT_REQUESTED path={OUTPUT}")
