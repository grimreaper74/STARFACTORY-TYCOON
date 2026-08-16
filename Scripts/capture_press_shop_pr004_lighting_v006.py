"""Capture fixed-camera visual evidence for PR-004 lighting candidate v006."""

import os
import time
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004LightingCandidate_v006"
CAPTURES = {
    "whole": ("LB_CAM_PressShop_ManagementOverview", "press_shop_v006_whole.png"),
    "front_end": ("LB_INT_PR004_V009_CAM_FrontEndDirty", "press_shop_v006_front_end.png"),
    "pr004": ("LB_INT_PR004_V009_CAM_PR004CloseDirty", "press_shop_v006_pr004.png"),
}
capture_id = os.environ.get("LB_PRESS_V006_CAPTURE", "pr004").lower()
camera_label, filename = CAPTURES[capture_id]
output = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/PressShopIntegration/v006_pr004_lighting" / filename

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
camera = next((actor for actor in actors.get_all_level_actors() if actor.get_actor_label() == camera_label), None)
if camera is None:
    raise RuntimeError(f"Missing fixed camera {camera_label}")

output.parent.mkdir(parents=True, exist_ok=True)
if output.exists():
    output.unlink()
world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
unreal.SystemLibrary.execute_console_command(world, "r.HighResScreenshotDelay 28")
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()
task = unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, str(output), camera=camera, force_game_view=True)
if not task.is_valid_task():
    raise RuntimeError("Invalid screenshot task")

started = time.monotonic()
tick_handle = None


def finish(_delta):
    global tick_handle
    elapsed = time.monotonic() - started
    if elapsed >= 3.0 and output.exists() and output.stat().st_size >= 1024:
        unreal.log(f"LINE_BOSS_PRESS_V006_CAPTURE_PASS id={capture_id} path={output}")
    elif elapsed < 55.0:
        return
    else:
        unreal.log_error(f"LINE_BOSS_PRESS_V006_CAPTURE_FAIL id={capture_id}")
    if tick_handle is not None:
        unreal.unregister_slate_post_tick_callback(tick_handle)
        tick_handle = None
    unreal.SystemLibrary.quit_editor()


tick_handle = unreal.register_slate_post_tick_callback(finish)
