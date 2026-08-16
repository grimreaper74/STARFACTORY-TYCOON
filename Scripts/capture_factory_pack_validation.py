"""Request a fixed-camera screenshot of the curated Factory Environment kit."""

from pathlib import Path
import time

import unreal


MAP = "/Game/LineBoss/Developer/Validation/LB_FactoryPack_KitValidation"
CAMERA = "LB_CAM_FactoryPack_Kit"
OUTPUT = (
    Path(unreal.Paths.project_saved_dir())
    / "ValidationScreenshots/Vendor/factory_environment_shortlist_v001.png"
)

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels.load_level(MAP)
camera = next(
    (actor for actor in actors.get_all_level_actors() if actor.get_actor_label() == CAMERA),
    None,
)
if camera is None:
    raise RuntimeError(f"Missing fixed validation camera {CAMERA}")

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
unreal.SystemLibrary.execute_console_command(world, "r.ForceDebugViewModes 0")
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()
task = unreal.AutomationLibrary.take_high_res_screenshot(
    1920,
    1080,
    str(OUTPUT),
    camera=camera,
    mask_enabled=False,
    capture_hdr=False,
    comparison_tolerance=unreal.ComparisonTolerance.LOW,
    comparison_notes="Line Boss curated Factory Environment shortlist",
    delay=0.0,
    force_game_view=True,
)
if not task.is_valid_task():
    raise RuntimeError("Unreal did not create a valid Factory Environment screenshot task")
unreal.log(f"LINE_BOSS_FACTORY_PACK_SCREENSHOT_REQUESTED camera={CAMERA} path={OUTPUT}")

# This script also runs through UnrealEditor.exe without a visible window. Keep
# Slate ticking until the latent automation screenshot has finished, then close
# the temporary editor process cleanly.
started = time.monotonic()
tick_handle = None


def finish_when_ready(_delta_seconds):
    global tick_handle
    if not task.is_task_done() and time.monotonic() - started < 45.0:
        return
    if OUTPUT.exists() and OUTPUT.stat().st_size >= 1024:
        unreal.log(
            f"LINE_BOSS_FACTORY_PACK_SCREENSHOT_PASS path={OUTPUT} bytes={OUTPUT.stat().st_size}"
        )
    else:
        unreal.log_error(f"LINE_BOSS_FACTORY_PACK_SCREENSHOT_FAIL path={OUTPUT}")
    if tick_handle is not None:
        unreal.unregister_slate_post_tick_callback(tick_handle)
        tick_handle = None
    unreal.SystemLibrary.quit_editor()


tick_handle = unreal.register_slate_post_tick_callback(finish_when_ready)
