"""Capture one deterministic Train A v012 motion/state view per Unreal process."""

import os
import json
import time
from pathlib import Path

import unreal


unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP = os.environ.get("LB_PTA_CAPTURE_MAP", "/Game/LineBoss/Maps/LB_PressTrainAMotionCandidate_v012")
CAPTURE_LABEL = os.environ.get("LB_PTA_CAPTURE_LABEL", "v012").lower()
MODE = os.environ.get("LB_PTA_CAPTURE_MODE",
                      os.environ.get("LB_PRESS_TRAIN_A_MOTION_V012_CAPTURE", "s02")).lower()
VIEWS = {
    "s02": ("CA_MW_PTA_CAM_Mechanics_v009", "press_train_a_motion_v012_s02_draw.png",
            (2600, 750, 1250), (0, 750, 380)),
    "s04": ("CA_MW_PTA_CAM_Mechanics_v009", "press_train_a_motion_v012_s04_trim.png",
            (2600, 2250, 1250), (0, 2250, 380)),
    "unload": ("CA_MW_PTA_CAM_S07_v009", "press_train_a_motion_v012_s07_unload.png",
               (2400, 5500, 1250), (-500, 4720, 360)),
    "fault": ("CA_MW_PTA_CAM_Mechanics_v009", "press_train_a_motion_v012_access_fault_hmi.png",
              (2600, 2250, 1200), (300, 2250, 300)),
}
if MODE not in VIEWS:
    raise RuntimeError(MODE)
CAMERA_LABEL, FILENAME, CAMERA_LOCATION, CAMERA_TARGET = VIEWS[MODE]
if CAPTURE_LABEL != "v012":
    FILENAME = FILENAME.replace("v012", CAPTURE_LABEL)
    if MODE in ("s02", "s04"):
        CAMERA_LOCATION = (1400, CAMERA_LOCATION[1], 620)
        CAMERA_TARGET = (0, CAMERA_TARGET[1], 270)
    elif MODE == "unload":
        CAMERA_LOCATION = (-1300, 5250, 700)
        CAMERA_TARGET = (-250, 4700, 220)
    elif MODE == "fault":
        CAMERA_LOCATION = (1250, 4150, 420)
        CAMERA_TARGET = (644, 4150, 260)


def vector_override(name, fallback):
    value = os.environ.get(name)
    if not value:
        return fallback
    parts = tuple(float(part.strip()) for part in value.split(","))
    if len(parts) != 3:
        raise RuntimeError(f"{name} must contain exactly three comma-separated values")
    return parts


CAMERA_LOCATION = vector_override("LB_PTA_CAPTURE_CAMERA_LOCATION", CAMERA_LOCATION)
CAMERA_TARGET = vector_override("LB_PTA_CAPTURE_CAMERA_TARGET", CAMERA_TARGET)
CAMERA_FOV = float(os.environ.get("LB_PTA_CAPTURE_CAMERA_FOV", "48.0"))
HIERARCHY_OUTPUT = os.environ.get("LB_PTA_CAPTURE_HIERARCHY_OUTPUT")
OUTPUT_DIRECTORY = os.environ.get(
    "LB_PTA_CAPTURE_OUTPUT_DIRECTORY", f"ValidationScreenshots/PressShopIntegration/press_train_a_motion_{CAPTURE_LABEL}")
OUTPUT = Path(unreal.Paths.project_saved_dir()) / OUTPUT_DIRECTORY / FILENAME
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
        unreal.log_error(f"PRESS_TRAIN_A_MOTION_{CAPTURE_LABEL.upper()}_CAPTURE_FAIL mode={MODE} reason={failure}")
    else:
        unreal.log(f"PRESS_TRAIN_A_MOTION_{CAPTURE_LABEL.upper()}_CAPTURE_PASS mode={MODE} output={OUTPUT}")
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
    if MODE == "s02":
        ready = "DRAW_S02" in phase_name and 0.18 <= status.cycle_progress <= 0.22
    elif MODE == "s04":
        ready = "TRIM_S04" in phase_name and 0.50 <= status.cycle_progress <= 0.54
    elif MODE == "unload":
        # Unload uses TransferWave(0.91, 0.97), whose maximum articulation is at 0.94.
        # Capture the narrow peak window rather than the descending/rest side of the phase.
        ready = "UNLOAD_AND_INSPECT" in phase_name and 0.938 <= status.cycle_progress <= 0.945
    elif MODE == "fault":
        if not fault_commanded and status.cycle_progress >= 0.30:
            station.set_access_interlocks_closed(False)
            fault_commanded = True
        ready = fault_commanded and "FAULT" in str(status.state).upper()
    if not ready:
        return

    location = unreal.Vector(*CAMERA_LOCATION)
    target = unreal.Vector(*CAMERA_TARGET)
    camera.set_actor_location(location, False, False)
    camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(location, target), False)
    camera.camera_component.set_editor_property("field_of_view", CAMERA_FOV)
    if HIERARCHY_OUTPUT:
        hierarchy_path = Path(unreal.Paths.project_dir()) / HIERARCHY_OUTPUT
        hierarchy_path.parent.mkdir(parents=True, exist_ok=True)
        hierarchy = []
        for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.StaticMeshActor):
            actor_tags = {str(value) for value in actor.tags}
            roles = sorted(value for value in actor_tags if value.startswith("LB.PressTrain.Role.unload_robot_"))
            if not roles:
                continue
            location = actor.get_actor_location()
            rotation = actor.get_actor_rotation()
            component = actor.root_component
            relative_location = component.get_editor_property("relative_location")
            relative_rotation = component.get_editor_property("relative_rotation")
            parent = actor.get_attach_parent_actor()
            hierarchy.append({
                "actor": actor.get_actor_label(), "roles": roles,
                "parent": parent.get_actor_label() if parent else None,
                "world_location_cm": [location.x, location.y, location.z],
                "world_rotation_deg": [rotation.roll, rotation.pitch, rotation.yaw],
                "relative_location_cm": [relative_location.x, relative_location.y, relative_location.z],
                "relative_rotation_deg": [relative_rotation.roll, relative_rotation.pitch, relative_rotation.yaw],
                "mobility": str(component.get_editor_property("mobility")),
            })
        hierarchy_path.write_text(json.dumps({"mode": MODE, "phase": phase_name,
                                              "cycle_progress": status.cycle_progress,
                                              "hierarchy": hierarchy}, indent=2), encoding="utf-8")
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
