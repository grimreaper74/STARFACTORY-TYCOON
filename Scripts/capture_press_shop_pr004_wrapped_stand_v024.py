"""Capture one fixed-camera v024 simplified PR-004 view per Unreal process."""

import os
import time
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004WrappedStandCandidate_v024"
VIEWS = {
    "front": ("LB_INT_PR004_V009_CAM_FrontEndDirty", "press_shop_v024_front.png"),
    "pr004": ("LB_INT_PR004_V009_CAM_PR004CloseDirty", "press_shop_v024_pr004.png"),
}
key = os.environ.get("LB_PRESS_V024_CAPTURE", "front").lower()
if key not in VIEWS:
    raise RuntimeError(f"Unknown v024 capture key: {key}")
camera_label, filename = VIEWS[key]
output = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/PressShopIntegration/v024_pr004_wrapped_stand" / filename
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
handle = None


def tick(_delta_seconds):
    global handle
    elapsed = time.monotonic() - started
    if elapsed >= 3.0 and output.exists() and output.stat().st_size >= 1024:
        unreal.log(f"LINE_BOSS_PRESS_V024_CAPTURE_PASS view={key} output={output}")
    elif elapsed < 55.0:
        return
    else:
        unreal.log_error(f"LINE_BOSS_PRESS_V024_CAPTURE_FAIL view={key} output={output}")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.SystemLibrary.quit_editor()


handle = unreal.register_slate_post_tick_callback(tick)
