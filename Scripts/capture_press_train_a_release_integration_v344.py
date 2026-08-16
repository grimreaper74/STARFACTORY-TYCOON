"""Capture fresh fixed-camera v343 release-integration evidence, one view per process."""
import os
import time
from pathlib import Path

import unreal


unreal.EditorPythonScripting.set_keep_python_script_alive(True)
view = os.environ.get("LB_V344_VIEW", "operator").lower()
views = {
    "operator": "LB_V301_CAM_TrainAOperatorClear",
    "overview": "LB_V295_CAM_TrainAOverview",
}
if view not in views:
    raise RuntimeError(f"Unknown v344 view {view}")
map_path = "/Game/LineBoss/Maps/LB_PressShop_TrainAReleaseIntegrationCandidate_v343"
out = Path(unreal.Paths.project_saved_dir()) / f"ValidationScreenshots/PressShopIntegration/v344_train_a_release_integration/{view}.png"
if out.exists():
    raise RuntimeError(f"Refusing to overwrite {out}")
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(map_path):
    raise RuntimeError(map_path)
camera = next((a for a in actors_api.get_all_level_actors() if a.get_actor_label() == views[view]), None)
if camera is None:
    raise RuntimeError(views[view])
out.parent.mkdir(parents=True, exist_ok=True)
world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()
task = unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, str(out), camera=camera, force_game_view=True, delay=15)
if not task.is_valid_task():
    raise RuntimeError("Invalid v344 screenshot task")
started = time.monotonic()
handle = None


def tick(_):
    global handle
    elapsed = time.monotonic() - started
    if elapsed >= 16 and out.exists() and out.stat().st_size >= 1024:
        unreal.log(f"LB_TRAIN_A_V344_CAPTURE_PASS view={view} path={out}")
    elif elapsed < 90:
        return
    else:
        unreal.log_error(f"LB_TRAIN_A_V344_CAPTURE_FAIL view={view}")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.execute_console_command(world, "QUIT_EDITOR")


handle = unreal.register_slate_post_tick_callback(tick)
