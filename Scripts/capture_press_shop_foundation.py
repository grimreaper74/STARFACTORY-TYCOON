"""Capture a current fixed camera from the Press Shop foundation map."""

import os
import time
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_Foundation"
CAPTURES = {
    "management": ("LB_CAM_PressShop_ManagementOverview", "press_shop_management_current_v001.png"),
    "top": ("LB_CAM_PressShop_TopDown", "press_shop_top_current_v001.png"),
}
capture_id = os.environ.get("LB_CAPTURE_CAMERA", "management").lower()
if capture_id not in CAPTURES:
    raise RuntimeError(f"Unknown foundation capture {capture_id}")
camera_label, filename = CAPTURES[capture_id]
output = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/PressShop" / filename

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels.load_level(MAP)
camera = next((actor for actor in actors.get_all_level_actors() if actor.get_actor_label() == camera_label), None)
if camera is None:
    raise RuntimeError(f"Missing fixed camera {camera_label}")

output.parent.mkdir(parents=True, exist_ok=True)
world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()
task = unreal.AutomationLibrary.take_high_res_screenshot(
    1920, 1080, str(output), camera=camera, mask_enabled=False, capture_hdr=False,
    comparison_tolerance=unreal.ComparisonTolerance.LOW,
    comparison_notes=f"Line Boss Press Shop current foundation: {capture_id}",
    delay=0.0, force_game_view=True,
)
if not task.is_valid_task():
    raise RuntimeError("Unreal did not create a valid foundation screenshot task")
unreal.log(f"LINE_BOSS_PRESS_SHOP_SCREENSHOT_REQUESTED camera={camera_label} path={output}")

started = time.monotonic()
tick_handle = None


def finish_when_ready(_delta_seconds):
    global tick_handle
    if not task.is_task_done() and time.monotonic() - started < 45.0:
        return
    if output.exists() and output.stat().st_size >= 1024:
        unreal.log(f"LINE_BOSS_PRESS_SHOP_SCREENSHOT_PASS path={output} bytes={output.stat().st_size}")
    else:
        unreal.log_error(f"LINE_BOSS_PRESS_SHOP_SCREENSHOT_FAIL path={output}")
    if tick_handle is not None:
        unreal.unregister_slate_post_tick_callback(tick_handle)
        tick_handle = None
    unreal.SystemLibrary.quit_editor()


tick_handle = unreal.register_slate_post_tick_callback(finish_when_ready)
