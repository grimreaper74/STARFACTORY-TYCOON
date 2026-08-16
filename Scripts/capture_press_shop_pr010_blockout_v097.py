"""Capture one fixed PR-010 v097 blockout view per clean Unreal process."""

import os
import time
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR010BlockoutCandidate_v097"
CAPTURES = {
    "overview": ("LB_PR010_V097_CAM_Overview", "press_shop_v097_pr010_blockout_overview.png"),
    "infeed": ("LB_PR010_V097_CAM_Infeed", "press_shop_v097_pr010_blockout_infeed.png"),
    "handoff": ("LB_PR010_V097_CAM_LaneHandoff", "press_shop_v097_pr010_blockout_handoff.png"),
    "elevated": ("LB_PR010_V097_CAM_Elevated", "press_shop_v097_pr010_blockout_elevated.png"),
}
capture_id = os.environ.get("LB_PR010_V097_CAPTURE", "overview").lower()
if capture_id not in CAPTURES: raise RuntimeError(capture_id)
camera_label, filename = CAPTURES[capture_id]
output = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/PressShopIntegration/v097_pr010_blockout" / filename

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP): raise RuntimeError(MAP)
camera = next((actor for actor in actors.get_all_level_actors() if actor.get_actor_label() == camera_label), None)
if camera is None: raise RuntimeError(camera_label)
output.parent.mkdir(parents=True, exist_ok=True)
if output.exists(): output.unlink()
world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
unreal.SystemLibrary.execute_console_command(world, "r.HighResScreenshotDelay 28")
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()
task = unreal.AutomationLibrary.take_high_res_screenshot(
    1920, 1080, str(output), camera=camera, mask_enabled=False, capture_hdr=False,
    comparison_tolerance=unreal.ComparisonTolerance.LOW,
    comparison_notes=f"Cairnwell PR-010 v097 four-lane engineering blockout: {capture_id}",
    delay=0.0, force_game_view=True)
if not task.is_valid_task(): raise RuntimeError(f"Invalid screenshot task for {capture_id}")
started = time.monotonic()
handle = None


def finish(_delta):
    global handle
    elapsed = time.monotonic() - started
    if elapsed >= 3.0 and output.exists() and output.stat().st_size >= 1024:
        unreal.log(f"PR010_V097_CAPTURE_PASS id={capture_id} path={output}")
    elif elapsed < 55.0:
        return
    else:
        unreal.log_error(f"PR010_V097_CAPTURE_FAIL id={capture_id} path={output}")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.SystemLibrary.quit_editor()


handle = unreal.register_slate_post_tick_callback(finish)
