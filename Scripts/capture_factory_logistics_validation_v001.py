"""Capture the isolated licensed logistics shortlist validation bay."""

from pathlib import Path
import time

import unreal


unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP = "/Game/LineBoss/Developer/Validation/LB_FactoryLogistics_Candidate_v001"
CAMERA = "LB_CAM_FactoryLogistics_v001"
OUTPUT = Path(unreal.Paths.project_saved_dir()) / (
    "ValidationScreenshots/Vendor/factory_logistics_shortlist_v001.png")
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
camera = next((actor for actor in actors.get_all_level_actors()
               if actor.get_actor_label() == CAMERA), None)
if camera is None:
    raise RuntimeError(f"Missing fixed camera {CAMERA}")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()
task = unreal.AutomationLibrary.take_high_res_screenshot(
    1920, 1080, str(OUTPUT), camera=camera, mask_enabled=False,
    capture_hdr=False, comparison_tolerance=unreal.ComparisonTolerance.LOW,
    comparison_notes="Line Boss contained Factory Environment logistics shortlist",
    delay=0.0, force_game_view=True)
if not task.is_valid_task():
    raise RuntimeError("Unreal did not create a valid logistics screenshot task")
started = time.monotonic()
tick_handle = None


def finish_when_ready(_delta_seconds):
    global tick_handle
    if not task.is_task_done() and time.monotonic() - started < 45.0:
        return
    if OUTPUT.exists() and OUTPUT.stat().st_size >= 1024:
        unreal.log(f"LINE_BOSS_FACTORY_LOGISTICS_SCREENSHOT_PASS path={OUTPUT}")
    else:
        unreal.log_error(f"LINE_BOSS_FACTORY_LOGISTICS_SCREENSHOT_FAIL path={OUTPUT}")
    if tick_handle is not None:
        unreal.unregister_slate_post_tick_callback(tick_handle)
        tick_handle = None
    unreal.SystemLibrary.quit_editor()


tick_handle = unreal.register_slate_post_tick_callback(finish_when_ready)

