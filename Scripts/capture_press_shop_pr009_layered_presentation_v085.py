"""Capture one fixed v085 layered PR-009 editor-world image per process."""
import os
import time
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR009LayeredPresentationCandidate_v085"
CAPTURES = {
    "process": ("LB_PR009_V085_PRESENT_CAM_Process", "press_shop_v085_pr009_layered_process.png"),
    "interface": ("LB_PR009_V085_PRESENT_CAM_Interface", "press_shop_v085_pr009_layered_interface.png"),
    "cell": ("LB_PR009_V085_PRESENT_CAM_CellHero", "press_shop_v085_pr009_layered_cell.png"),
    "elevated": ("LB_PR009_V085_PRESENT_CAM_Elevated", "press_shop_v085_pr009_layered_elevated.png"),
}
capture_id = os.environ.get("LB_PR009_V085_CAPTURE", "cell").lower()
camera_label, filename = CAPTURES[capture_id]
output = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/PressShopIntegration/v085_pr009_layered" / filename

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
task = unreal.AutomationLibrary.take_high_res_screenshot(
    1920, 1080, str(output), camera=camera, mask_enabled=False, capture_hdr=False,
    comparison_tolerance=unreal.ComparisonTolerance.LOW,
    comparison_notes=f"Cairnwell PR-009 layered v085 fixed review: {capture_id}",
    delay=0.0, force_game_view=True,
)
if not task.is_valid_task():
    raise RuntimeError(f"Invalid v085 screenshot task for {capture_id}")

started = time.monotonic()
tick_handle = None


def finish(_delta):
    global tick_handle
    elapsed = time.monotonic() - started
    if elapsed >= 3.0 and output.exists() and output.stat().st_size >= 1024:
        unreal.log(f"CAIRNWELL_PR009_V085_CAPTURE_PASS id={capture_id} path={output}")
    elif elapsed < 55.0:
        return
    else:
        unreal.log_error(f"CAIRNWELL_PR009_V085_CAPTURE_FAIL id={capture_id} path={output}")
    if tick_handle is not None:
        unreal.unregister_slate_post_tick_callback(tick_handle)
        tick_handle = None
    unreal.SystemLibrary.quit_editor()


tick_handle = unreal.register_slate_post_tick_callback(finish)
