"""Capture one deterministic v016 reusable-robot view per process."""

import os
import time
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004ReusableRobotPlateCandidate_v019"
VIEWS = {
    "close": ("LB_AUDIT_PR004_ToolAttachment_Close_v014", "pr004_v019_robot_plate_close.png"),
    "cell": ("LB_INT_PR004_V009_CAM_PR004CloseDirty", "pr004_v019_cell.png"),
}
key = os.environ.get("LB_PR004_V016_CAPTURE", "close")
label, name = VIEWS[key]
out = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/PressShopIntegration/v019_pr004_robot_plate" / name
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
camera = next((a for a in actor_subsystem.get_all_level_actors() if a.get_actor_label() == label), None)
if camera is None:
    raise RuntimeError(f"Missing camera {label}")
out.parent.mkdir(parents=True, exist_ok=True)
if out.exists():
    out.unlink()
world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
unreal.SystemLibrary.execute_console_command(world, "r.HighResScreenshotDelay 28")
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()
task = unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, str(out), camera=camera, force_game_view=True)
if not task.is_valid_task():
    raise RuntimeError("Invalid screenshot task")
started = time.monotonic()
handle = None


def tick(_dt):
    global handle
    elapsed = time.monotonic() - started
    if elapsed >= 3.0 and out.exists() and out.stat().st_size >= 1024:
        unreal.log(f"LINE_BOSS_PR004_REUSABLE_ROBOT_CAPTURE_V016_PASS view={key} output={out}")
    elif elapsed < 55.0:
        return
    else:
        unreal.log_error(f"LINE_BOSS_PR004_REUSABLE_ROBOT_CAPTURE_V016_FAIL view={key}")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.SystemLibrary.quit_editor()


handle = unreal.register_slate_post_tick_callback(tick)
