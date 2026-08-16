"""Capture a retained fixed camera from one isolated B-D variant in PIE.

This deliberately captures the live duplicated world rather than the editor
world.  UE 5.8's FunctionalTesting screenshot path is unstable when invoked
against an editor-only world, while the retained Train A evidence path is
proven in PIE.
"""

import os
import time
from pathlib import Path

import unreal


unreal.EditorPythonScripting.set_keep_python_script_alive(True)
LETTER = os.environ.get("LB_PT_VARIANT", "").upper()
VIEW = os.environ.get("LB_PT_VARIANT_VIEW", "hero").lower()
if LETTER not in {"B", "C", "D"}:
    raise RuntimeError("LB_PT_VARIANT must be B, C or D")
VIEWS = {
    "hero": "CA_MW_PTA_CAM_Hero_v009",
    "overhead": "CA_MW_PTA_CAM_Overhead_v009",
    "operator_side": "CA_MW_PTA_CAM_OperatorSide_v009",
    "mechanics": "CA_MW_PTA_CAM_Mechanics_v009",
}
if VIEW not in VIEWS:
    raise RuntimeError(f"unknown view {VIEW}")

MAP = os.environ.get(
    "LB_PT_VARIANT_MAP",
    f"/Game/LineBoss/Maps/LB_PressTrain{LETTER}IsolatedVariantCandidate_v001")
CAMERA_LABEL = VIEWS[VIEW]
OUTPUT_LABEL = os.environ.get(
    "LB_PT_VARIANT_OUTPUT_LABEL", f"{LETTER.lower()}_variant_v001")
OUTPUT_DIRECTORY = os.environ.get(
    "LB_PT_VARIANT_OUTPUT_DIRECTORY",
    f"ValidationScreenshots/PressShopIntegration/press_train_{OUTPUT_LABEL}")
OUTPUT = Path(unreal.Paths.project_saved_dir()) / OUTPUT_DIRECTORY / (
    f"press_train_{OUTPUT_LABEL}_{VIEW}_runtime.png")

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
if OUTPUT.exists():
    OUTPUT.unlink()
unreal.EditorLevelLibrary.editor_play_simulate()
started = time.monotonic()
capture_started = None
handle = None


def stop(failure=None):
    global handle
    logger = unreal.log_error if failure else unreal.log
    result = "FAIL" if failure else "PASS"
    detail = failure if failure else f"output={OUTPUT}"
    logger(f"PRESS_TRAIN_{LETTER}_VARIANT_V001_WIDE_CAPTURE_{result} view={VIEW} {detail}")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()


def tick(_delta_seconds):
    global capture_started
    now = time.monotonic()
    if now - started > 70.0:
        stop("timeout")
        return
    world = unreal.EditorLevelLibrary.get_game_world()
    if world is None:
        return
    if capture_started is None:
        cameras = [
            actor for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.CameraActor)
            if actor.get_actor_label() == CAMERA_LABEL
        ]
        stations = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBPressTrainAStation)
        if len(cameras) != 1 or len(stations) != 1:
            if now - started < 8.0:
                return
            stop(f"cameras={len(cameras)} stations={len(stations)}")
            return
        station = stations[0]
        train_id = str(station.get_editor_property("train_id")).upper()
        if train_id != f"TRAIN_{LETTER}":
            stop(f"wrong train identity {train_id}")
            return
        unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
        unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
        unreal.SystemLibrary.execute_console_command(world, "r.HighResScreenshotDelay 12")
        unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
        unreal.AutomationLibrary.finish_loading_before_screenshot()
        task = unreal.AutomationLibrary.take_high_res_screenshot(
            1920, 1080, str(OUTPUT), camera=cameras[0], mask_enabled=False,
            capture_hdr=False, force_game_view=True)
        if not task.is_valid_task():
            stop("invalid screenshot task")
            return
        capture_started = now
        return
    if OUTPUT.exists() and OUTPUT.stat().st_size >= 1024:
        stop()
    elif now - capture_started > 55.0:
        stop("screenshot output missing")


handle = unreal.register_slate_post_tick_callback(tick)
