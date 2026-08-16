"""Capture current whole-shop integration evidence without showing the editor."""

import os
import time
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_IntegrationCandidate_v002"
CAPTURES = {
    "whole": ("LB_CAM_PressShop_ManagementOverview", "press_shop_integrated_whole_v002.png"),
    "player": ("LB_INT_PR005_CAM_PlayerFrontEnd", "press_shop_integrated_player_v002.png"),
    "pr005": ("LB_INT_PR005_CAM_Context", "press_shop_integrated_pr005_v002.png"),
    "front_end": ("LB_INT_FRONT_CAM_FrontEndOverview", "press_shop_front_end_overview_v002.png"),
    "coil_store": ("LB_INT_FRONT_CAM_CoilStoreCrane", "press_shop_coil_store_crane_v002.png"),
    "receipt": ("LB_INT_FRONT_CAM_PR001_PR002", "press_shop_pr001_pr002_v002.png"),
    "front_top": ("LB_INT_FRONT_CAM_FrontEndTop", "press_shop_front_end_top_v002.png"),
    "crane_detail": ("LB_INT_FRONT_CAM_CraneDetail", "press_shop_crane_detail_v002.png"),
    "pr004_prep": ("LB_INT_FRONT_CAM_PR004Prep", "press_shop_pr004_prep_v002.png"),
    "front_eye": ("LB_INT_FRONT_CAM_FrontEndEyeLevel", "press_shop_front_end_eye_level_v002.png"),
}
capture_id = os.environ.get("LB_CAPTURE_CAMERA", "player").lower()
if capture_id not in CAPTURES:
    raise RuntimeError(f"Unknown integration capture {capture_id}")
camera_label, filename = CAPTURES[capture_id]
output = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/PressShopIntegration" / filename

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels.load_level(MAP)
camera = next((actor for actor in actors.get_all_level_actors() if actor.get_actor_label() == camera_label), None)
if camera is None:
    raise RuntimeError(f"Missing fixed integration camera {camera_label}")
output.parent.mkdir(parents=True, exist_ok=True)
# A stale screenshot must never satisfy this validation gate. The path is a
# fixed file inside Saved/ValidationScreenshots, so replacing it is scoped and
# intentional evidence generation rather than project-asset deletion.
if output.exists():
    output.unlink()
world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
unreal.SystemLibrary.execute_console_command(world, "r.Lumen.ScreenProbeGather.Temporal.MaxFramesAccumulated 32")
warmup_frames = int(os.environ.get("LB_CAPTURE_WARMUP_FRAMES", "32"))
unreal.SystemLibrary.execute_console_command(world, f"r.HighResScreenshotDelay {warmup_frames}")
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()

# Asset loading alone does not converge Lumen/TAA. Earlier validation frames
# showed first-frame wall smearing and black machinery. The renderer's native
# high-resolution frame delay keeps the immediate automation task alive while
# temporal systems converge; using the task's Python delay lets the commandlet
# exit before rendering begins.
task = unreal.AutomationLibrary.take_high_res_screenshot(
    1920, 1080, str(output), camera=camera, mask_enabled=False, capture_hdr=False,
    comparison_tolerance=unreal.ComparisonTolerance.LOW,
    comparison_notes=f"Line Boss integrated Press Shop: {capture_id}",
    delay=0.0, force_game_view=True,
)
if not task.is_valid_task():
    raise RuntimeError("Unreal did not create a valid integration screenshot task")
capture_started = time.monotonic()
unreal.log(
    f"LINE_BOSS_PRESS_SHOP_INTEGRATION_SCREENSHOT_REQUESTED "
    f"camera={camera_label} warmup_frames={warmup_frames} path={output}"
)
tick_handle = None


def finish_when_ready(_delta_seconds):
    global tick_handle
    now = time.monotonic()
    elapsed = now - capture_started
    if output.exists() and output.stat().st_size >= 1024:
        unreal.log(f"LINE_BOSS_PRESS_SHOP_INTEGRATION_SCREENSHOT_PASS path={output} bytes={output.stat().st_size}")
    elif elapsed < 55.0:
        return
    else:
        unreal.log_error(f"LINE_BOSS_PRESS_SHOP_INTEGRATION_SCREENSHOT_FAIL path={output}")
    if tick_handle is not None:
        unreal.unregister_slate_post_tick_callback(tick_handle)
        tick_handle = None
    unreal.SystemLibrary.quit_editor()


tick_handle = unreal.register_slate_post_tick_callback(finish_when_ready)
