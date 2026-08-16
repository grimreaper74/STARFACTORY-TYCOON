"""Capture one deterministic PR-004 v020 Surface Forge robot view per editor process.

This script is evidence-only: it loads the isolated v020 candidate map and never
modifies or saves the accepted PR-004 v006 integration baseline.
"""

import os
import time
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004SurfaceForgeRobotCandidate_v020"
VIEWS = {
    "detail": ("LB_AUDIT_PR004_ToolAttachment_Close_v014", "pr004_v020_robot_detail.png"),
    "cell": ("LB_INT_PR004_V009_CAM_PR004CloseDirty", "pr004_v020_cell.png"),
    "front": ("LB_INT_PR004_V009_CAM_FrontEndDirty", "pr004_v020_front.png"),
}

key = os.environ.get("LB_PR004_V020_CAPTURE", "detail")
if key not in VIEWS:
    raise RuntimeError(f"Unknown LB_PR004_V020_CAPTURE view: {key}")

label, filename = VIEWS[key]
output = (
    Path(unreal.Paths.project_saved_dir())
    / "ValidationScreenshots/PressShopIntegration/v020_pr004_surfaceforge_robot"
    / filename
)

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load candidate map {MAP}")

camera = next(
    (actor for actor in actors.get_all_level_actors() if actor.get_actor_label() == label),
    None,
)
if camera is None:
    available = sorted(
        actor.get_actor_label()
        for actor in actors.get_all_level_actors()
        if "CAM" in actor.get_actor_label() or "AUDIT" in actor.get_actor_label()
    )
    raise RuntimeError(f"Missing camera {label}; available={available}")

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
task = unreal.AutomationLibrary.take_high_res_screenshot(
    1920,
    1080,
    str(output),
    camera=camera,
    force_game_view=True,
)
if not task.is_valid_task():
    raise RuntimeError("Invalid screenshot task")

started = time.monotonic()
handle = None


def tick(_delta_seconds):
    global handle
    elapsed = time.monotonic() - started
    if elapsed >= 3.0 and output.exists() and output.stat().st_size >= 1024:
        unreal.log(
            f"LINE_BOSS_PR004_SURFACEFORGE_V020_CAPTURE_PASS "
            f"view={key} output={output}"
        )
    elif elapsed < 55.0:
        return
    else:
        unreal.log_error(
            f"LINE_BOSS_PR004_SURFACEFORGE_V020_CAPTURE_FAIL "
            f"view={key} output={output}"
        )

    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.SystemLibrary.quit_editor()


handle = unreal.register_slate_post_tick_callback(tick)
