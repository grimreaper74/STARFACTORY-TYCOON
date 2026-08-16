"""Capture one of seven exact-map Train A v064 views per Unreal process."""

import os
import time
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressTrainADockCouplingEvidenceCandidate_v064"
CAPTURES = {
    "hero": ("CA_MW_PTA_CAM_Hero", "press_train_a_v064_hero.png"),
    "overview": ("CA_MW_PTA_CAM_Overview", "press_train_a_v064_overview.png"),
    "draw": ("CA_MW_PTA_CAM_DrawStage", "press_train_a_v064_draw_stage.png"),
    "service": ("CA_MW_PTA_CAM_DieChangeService", "press_train_a_v064_die_change_service.png"),
    "cart": ("CA_MW_PTA_CAM_DieCartDetail", "press_train_a_v064_die_cart_detail.png"),
    "s01": ("CA_MW_PTA_CAM_S01FeedEvidence_v064", "press_train_a_v064_s01_feed.png"),
    "s07": ("CA_MW_PTA_CAM_S07DischargeEvidence_v064", "press_train_a_v064_s07_discharge.png"),
}
capture_id = os.environ.get("LB_PRESS_TRAIN_A_V064_CAPTURE", "hero").lower()
if capture_id not in CAPTURES:
    raise RuntimeError(capture_id)
camera_label, filename = CAPTURES[capture_id]
output = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/PressShopIntegration/press_train_a_v064" / filename
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
    comparison_notes=f"Cairnwell Moorcross isolated Press Train A v064: {capture_id}",
    delay=0.0, force_game_view=True,
)
if not task.is_valid_task():
    raise RuntimeError(f"invalid screenshot task for {capture_id}")
started = time.monotonic()
handle = None


def finish(_delta):
    global handle
    elapsed = time.monotonic() - started
    if elapsed >= 3.0 and output.exists() and output.stat().st_size >= 1024:
        unreal.log(f"PRESS_TRAIN_A_V064_CAPTURE_PASS id={capture_id} path={output}")
    elif elapsed < 55.0:
        return
    else:
        unreal.log_error(f"PRESS_TRAIN_A_V064_CAPTURE_FAIL id={capture_id} path={output}")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.SystemLibrary.quit_editor()


handle = unreal.register_slate_post_tick_callback(finish)
