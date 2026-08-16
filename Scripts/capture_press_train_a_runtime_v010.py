"""Capture one fixed-camera Train A v010 runtime state per Unreal process."""

import os
import time
from pathlib import Path

import unreal


unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP = "/Game/LineBoss/Maps/LB_PressTrainARuntimeCandidate_v010"
MODE = os.environ.get("LB_PRESS_TRAIN_A_RUNTIME_V010_CAPTURE", "draw").lower()
VIEWS = {
    "draw": ("CA_MW_PTA_CAM_Hero_v009", "press_train_a_runtime_v010_draw_cycle.png"),
    "transfer": ("CA_MW_PTA_CAM_OperatorSide_v009", "press_train_a_runtime_v010_transfer_cycle.png"),
    "unload": ("CA_MW_PTA_CAM_S07_v009", "press_train_a_runtime_v010_unload_cycle.png"),
    "fault": ("CA_MW_PTA_CAM_OperatorSide_v009", "press_train_a_runtime_v010_access_fault.png"),
}
if MODE not in VIEWS:
    raise RuntimeError(MODE)
CAMERA_LABEL, FILENAME = VIEWS[MODE]
OUTPUT = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/PressShopIntegration/press_train_a_runtime_v010" / FILENAME
AUTHORITY = unreal.Name("CW.MW.CONTROL_ROOM")
SOURCE = unreal.Name("MW.MCR.TRAIN_A.CONSOLE")

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
if OUTPUT.exists():
    OUTPUT.unlink()
unreal.EditorLevelLibrary.editor_play_simulate()
started = time.monotonic()
configured = False
fault_commanded = False
capture_started = None
handle = None


def stop(failure=None):
    global handle
    if failure:
        unreal.log_error(f"PRESS_TRAIN_A_RUNTIME_V010_CAPTURE_FAIL mode={MODE} reason={failure}")
    else:
        unreal.log(f"PRESS_TRAIN_A_RUNTIME_V010_CAPTURE_PASS mode={MODE} output={OUTPUT}")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()


def wait_capture(_delta):
    if OUTPUT.exists() and OUTPUT.stat().st_size >= 1024:
        stop()
    elif time.monotonic() - capture_started > 80.0:
        stop("screenshot timeout")


def tick(_delta):
    global configured, fault_commanded, capture_started, handle
    if time.monotonic() - started > 45.0:
        stop("runtime capture window timeout")
        return
    world = unreal.EditorLevelLibrary.get_game_world()
    if world is None:
        return
    stations = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBPressTrainAStation)
    cameras = [actor for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.CameraActor)
               if actor.get_actor_label() == CAMERA_LABEL]
    if len(stations) != 1 or len(cameras) != 1:
        return
    station, camera = stations[0], cameras[0]
    if not configured:
        station.set_access_interlocks_closed(True)
        station.set_safety_circuit_healthy(True)
        station.set_emergency_stop_active(False)
        station.set_destack_healthy(True)
        station.set_transfer_healthy(True)
        station.set_hydraulic_pressure(280.0)
        station.set_press_load(45.0)
        station.set_inspection_healthy(True)
        station.set_stillage_output_clear(True)
        station.set_target_strokes_per_minute(10.0)
        if not station.queue_reserved_blank(unreal.Name("PTA-CAPTURE-RES-001"), unreal.Name("PR010-BLANK-CAPTURE-001")):
            stop("reserved blank refused")
            return
        if not station.queue_reserved_blank(unreal.Name("PTA-CAPTURE-RES-002"), unreal.Name("PR010-BLANK-CAPTURE-002")):
            stop("second reserved blank refused")
            return
        if not station.execute_remote_command(unreal.LBPressTrainACommand.POWER_ON, SOURCE, AUTHORITY):
            stop("power on refused")
            return
        if not station.execute_remote_command(unreal.LBPressTrainACommand.START, SOURCE, AUTHORITY):
            stop("start refused")
            return
        configured = True
        return

    status = station.get_hmi_status()
    phase_name = str(status.phase).upper()
    ready = False
    if MODE == "draw":
        ready = "DRAW_S02" in phase_name and 0.18 <= status.cycle_progress <= 0.22
    elif MODE == "transfer":
        ready = "TRANSFER_TO_S05" in phase_name and status.cycle_progress >= 0.60
    elif MODE == "unload":
        ready = "UNLOAD_AND_INSPECT" in phase_name and status.cycle_progress >= 0.94
    elif MODE == "fault":
        if not fault_commanded and status.cycle_progress >= 0.30:
            station.set_access_interlocks_closed(False)
            fault_commanded = True
        ready = fault_commanded and "FAULT" in str(status.state).upper()
    if not ready:
        return

    capture_started = time.monotonic()
    unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
    unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
    unreal.SystemLibrary.execute_console_command(world, "r.HighResScreenshotDelay 12")
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    unreal.AutomationLibrary.finish_loading_before_screenshot()
    unreal.unregister_slate_post_tick_callback(handle)
    handle = None
    task = unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, str(OUTPUT), camera=camera, force_game_view=True)
    if not task.is_valid_task():
        stop("invalid screenshot task")
        return
    handle = unreal.register_slate_post_tick_callback(wait_capture)


handle = unreal.register_slate_post_tick_callback(tick)

