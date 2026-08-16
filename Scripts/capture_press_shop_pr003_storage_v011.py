"""Capture one fixed-camera frame for PR-003 storage candidate v011."""

import os
import time
from pathlib import Path
import unreal

MAP = "/Game/LineBoss/Maps/LB_PressShop_PR003StorageCandidate_v014"
CAPTURES = {
    "front": ("LB_INT_PR004_V009_CAM_FrontEndDirty", "pr003_v011_front_end.png"),
    "whole": ("LB_CAM_PressShop_ManagementOverview", "pr003_v011_whole.png"),
}
capture_id = os.environ.get("LB_PR003_V011_CAPTURE", "front").lower()
camera_label, filename = CAPTURES[capture_id]
output = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/PressShopIntegration/v014_pr003_storage" / filename
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
camera = next((a for a in actors.get_all_level_actors() if a.get_actor_label() == camera_label), None)
if camera is None:
    raise RuntimeError(f"Missing fixed camera {camera_label}")
output.parent.mkdir(parents=True, exist_ok=True)
if output.exists(): output.unlink()
world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
unreal.SystemLibrary.execute_console_command(world, "r.HighResScreenshotDelay 28")
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()
task = unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, str(output), camera=camera, force_game_view=True)
if not task.is_valid_task(): raise RuntimeError("Invalid screenshot task")
started = time.monotonic(); tick_handle = None
def finish(_delta):
    global tick_handle
    elapsed = time.monotonic() - started
    if elapsed >= 3.0 and output.exists() and output.stat().st_size >= 1024:
        unreal.log(f"LINE_BOSS_PR003_V011_CAPTURE_PASS id={capture_id} path={output}")
    elif elapsed < 55.0: return
    else: unreal.log_error(f"LINE_BOSS_PR003_V011_CAPTURE_FAIL id={capture_id}")
    if tick_handle is not None:
        unreal.unregister_slate_post_tick_callback(tick_handle); tick_handle = None
    unreal.SystemLibrary.quit_editor()
tick_handle = unreal.register_slate_post_tick_callback(finish)
