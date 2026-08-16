"""Capture the early-gate v090 service-side hero camera."""

import time
from pathlib import Path
import unreal

MAP = "/Game/LineBoss/Maps/LB_PressShop_PR009ServiceCameraCandidate_v090"
CAMERA_LABEL = "LB_PR009_V090_PRESENT_CAM_ServiceHero"
OUTPUT = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/PressShopIntegration/v090_pr009_service_camera/press_shop_v090_pr009_service_camera_hero.png"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
camera = next((actor for actor in actors.get_all_level_actors() if actor.get_actor_label() == CAMERA_LABEL), None)
if camera is None:
    raise RuntimeError(CAMERA_LABEL)
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
if OUTPUT.exists():
    OUTPUT.unlink()
world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
unreal.SystemLibrary.execute_console_command(world, "r.HighResScreenshotDelay 28")
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()
task = unreal.AutomationLibrary.take_high_res_screenshot(
    1920, 1080, str(OUTPUT), camera=camera, mask_enabled=False, capture_hdr=False,
    comparison_tolerance=unreal.ComparisonTolerance.LOW,
    comparison_notes="Cairnwell PR-009 v090 south-west service-camera early gate",
    delay=0.0, force_game_view=True,
)
if not task.is_valid_task():
    raise RuntimeError("Invalid screenshot task")
started = time.monotonic()
handle = None

def finish(_delta):
    global handle
    elapsed = time.monotonic() - started
    if elapsed >= 3.0 and OUTPUT.exists() and OUTPUT.stat().st_size >= 1024:
        unreal.log(f"PR009_V090_SERVICE_CAMERA_CAPTURE_PASS path={OUTPUT}")
    elif elapsed < 55.0:
        return
    else:
        unreal.log_error(f"PR009_V090_SERVICE_CAMERA_CAPTURE_FAIL path={OUTPUT}")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.SystemLibrary.quit_editor()

handle = unreal.register_slate_post_tick_callback(finish)
