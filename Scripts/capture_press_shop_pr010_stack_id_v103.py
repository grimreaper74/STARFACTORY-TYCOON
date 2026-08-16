"""Capture the fixed v103 stack-ID evidence view in a clean Unreal process."""

import time
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR010ReleaseArtCandidate_v103"
CAMERA = "LB_PR010_V103_CAM_StackID"
output = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/PressShopIntegration/v103_pr010_release_art/press_shop_v103_pr010_stack_id.png"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
camera = next((actor for actor in actors.get_all_level_actors() if actor.get_actor_label() == CAMERA), None)
if camera is None:
    raise RuntimeError(CAMERA)
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
    1920, 1080, str(output), camera=camera, mask_enabled=False, capture_hdr=False,
    comparison_tolerance=unreal.ComparisonTolerance.LOW,
    comparison_notes="Cairnwell PR-010 v103 stack identity CCTV evidence",
    delay=0.0, force_game_view=True)
if not task.is_valid_task():
    raise RuntimeError("invalid v103 stack-ID screenshot task")
started = time.monotonic()
handle = None


def finish(_delta):
    global handle
    elapsed = time.monotonic() - started
    if elapsed >= 3.0 and output.exists() and output.stat().st_size >= 1024:
        unreal.log(f"PR010_V103_STACK_ID_CAPTURE_PASS path={output}")
    elif elapsed < 55.0:
        return
    else:
        unreal.log_error(f"PR010_V103_STACK_ID_CAPTURE_FAIL path={output}")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.SystemLibrary.quit_editor()


handle = unreal.register_slate_post_tick_callback(finish)
