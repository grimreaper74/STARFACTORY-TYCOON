"""Capture one of five exact-map fixed Train A v029 views per process."""

import os
import time
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressTrainACartMechanicalEvidenceCandidate_v029"
CAPTURES = {
    "hero": ("CA_MW_PTA_CAM_Hero", "press_train_a_v029_hero.png"),
    "overview": ("CA_MW_PTA_CAM_Overview", "press_train_a_v029_overview.png"),
    "draw": ("CA_MW_PTA_CAM_DrawStage", "press_train_a_v029_draw_stage.png"),
    "service": ("CA_MW_PTA_CAM_DieChangeService", "press_train_a_v029_die_change_service.png"),
    "cart": ("CA_MW_PTA_CAM_DieCartDetail", "press_train_a_v029_die_cart_detail.png"),
}
capture_id = os.environ.get("LB_PRESS_TRAIN_A_V029_CAPTURE", "cart").lower()
if capture_id not in CAPTURES:
    raise RuntimeError(capture_id)
camera_label, filename = CAPTURES[capture_id]
output = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/PressShopIntegration/press_train_a_v029" / filename
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
camera = next((actor for actor in actors.get_all_level_actors() if actor.get_actor_label() == camera_label), None)
if camera is None:
    raise RuntimeError(camera_label)
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
    comparison_notes=f"Cairnwell Moorcross isolated Press Train A v029: {capture_id}",
    delay=0.0, force_game_view=True)
if not task.is_valid_task():
    raise RuntimeError(f"invalid screenshot task for {capture_id}")
started = time.monotonic()
handle = None


def finish(_delta):
    global handle
    elapsed = time.monotonic() - started
    if elapsed >= 3.0 and output.exists() and output.stat().st_size >= 1024:
        unreal.log(f"PRESS_TRAIN_A_V029_CAPTURE_PASS id={capture_id} path={output}")
    elif elapsed < 55.0:
        return
    else:
        unreal.log_error(f"PRESS_TRAIN_A_V029_CAPTURE_FAIL id={capture_id} path={output}")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.SystemLibrary.quit_editor()


handle = unreal.register_slate_post_tick_callback(finish)
