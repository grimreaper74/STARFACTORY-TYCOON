"""Capture one fixed camera from isolated PR005 exterior integration v195."""

import os
import time
from pathlib import Path

import unreal


unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR005ExteriorIntegrationCandidate_v195"
VIEW = os.environ.get("LB_PR005_V195_CAPTURE", "operator_player").lower()
VIEWS = {
    "operator_player": "LB_PR005_V195_CAM_OperatorPlayer",
    "operator_elevated": "LB_PR005_V195_CAM_OperatorElevated",
    "service_side": "LB_PR005_V195_CAM_ServiceSide",
    "process_flow": "LB_PR005_V195_CAM_ProcessFlow",
}
if VIEW not in VIEWS:
    raise RuntimeError(VIEW)
OUT = Path(unreal.Paths.project_saved_dir()) / f"ValidationScreenshots/PressShopIntegration/pr005_exterior_integration_v195/pr005_v195_{VIEW}.png"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
OUT.parent.mkdir(parents=True, exist_ok=True)
if OUT.exists():
    OUT.unlink()
camera = next((actor for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
               if isinstance(actor, unreal.CameraActor) and actor.get_actor_label() == VIEWS[VIEW]), None)
if camera is None:
    raise RuntimeError(VIEWS[VIEW])
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()
task = unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, str(OUT), camera=camera, mask_enabled=False, capture_hdr=False, delay=0.0, force_game_view=True)
if not task.is_valid_task():
    raise RuntimeError("invalid screenshot task")
started = time.monotonic()
handle = None


def tick(_delta):
    global handle
    if OUT.exists() and OUT.stat().st_size >= 1024 and time.monotonic() - started > 3.0:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
        unreal.SystemLibrary.quit_editor()
    elif time.monotonic() - started > 45.0:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
        unreal.log_error(f"PR005 v195 capture timeout {VIEW}")
        unreal.SystemLibrary.quit_editor()


handle = unreal.register_slate_post_tick_callback(tick)
