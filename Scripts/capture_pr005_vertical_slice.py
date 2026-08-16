"""Capture one fixed PR-005 validation camera without opening the Unreal UI.

Set LB_CAPTURE_CAMERA to overview, process, or top before launching Unreal.
"""

import os
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Developer/Validation/LB_PR005_ModularValidation"
CAPTURES = {
    "overview": ("LB_CAM_PR005_Overview", "pr005_unreal_overview_v001.png"),
    "process": ("LB_CAM_PR005_Process", "pr005_unreal_process_v001.png"),
    "top": ("LB_CAM_PR005_Top", "pr005_unreal_top_v001.png"),
}

capture_id = os.environ.get("LB_CAPTURE_CAMERA", "overview").lower()
if capture_id not in CAPTURES:
    raise RuntimeError(f"Unknown LB_CAPTURE_CAMERA={capture_id!r}; expected {tuple(CAPTURES)}")

camera_label, filename = CAPTURES[capture_id]
output = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/PR005" / filename

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels.load_level(MAP)
camera = next((actor for actor in actors.get_all_level_actors() if actor.get_actor_label() == camera_label), None)
if camera is None:
    raise RuntimeError(f"Missing fixed camera {camera_label}")

output.parent.mkdir(parents=True, exist_ok=True)
world = unreal.EditorLevelLibrary.get_editor_world()
viewmode = os.environ.get("LB_CAPTURE_VIEWMODE", "lit").lower()
unreal.SystemLibrary.execute_console_command(world, f"viewmode {viewmode}")
unreal.SystemLibrary.execute_console_command(world, "r.ForceDebugViewModes 0")
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()
task = unreal.AutomationLibrary.take_high_res_screenshot(
    1920,
    1080,
    str(output),
    camera=camera,
    mask_enabled=False,
    capture_hdr=False,
    comparison_tolerance=unreal.ComparisonTolerance.LOW,
    comparison_notes=f"Line Boss PR-005 modular validation: {capture_id}",
    delay=0.0,
    force_game_view=True,
)
if not task.is_valid_task():
    raise RuntimeError("Unreal did not create a valid screenshot task")
unreal.log(f"LINE_BOSS_PR005_SCREENSHOT_REQUESTED camera={camera_label} path={output}")
