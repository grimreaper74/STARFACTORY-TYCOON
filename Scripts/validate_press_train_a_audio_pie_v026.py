"""Prove Train A spatial audio follows native state and phase in live PIE."""

import json
import time
from datetime import datetime, timezone
from pathlib import Path
import unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressTrainAAudioRuntimeCandidate_v026"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_audio_pie_v026.json"
AUTHORITY = unreal.Name("CW.MW.CONTROL_ROOM")
SOURCE = unreal.Name("MW.MCR.TRAIN_A.CONSOLE")
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not levels.load_level(MAP): raise RuntimeError(MAP)
unreal.EditorLevelLibrary.editor_play_simulate()
started = time.monotonic()
phase = "configure"
phase_started = started
evidence = {}
failures = []
handle = None


def component_rows(station):
    rows = {}
    for component in station.get_components_by_class(unreal.AudioComponent):
        sound = component.get_editor_property("sound")
        rows[component.get_name()] = {
            "sound": sound.get_path_name() if sound else None,
            "is_playing": bool(component.is_playing()),
            "allow_spatialization": bool(component.get_editor_property("allow_spatialization")),
            "override_attenuation": bool(component.get_editor_property("override_attenuation")),
            "volume_multiplier": component.get_editor_property("volume_multiplier"),
        }
    return rows


def snapshot(station):
    status = station.get_hmi_status()
    return {
        "state": str(status.state), "phase": str(status.phase),
        "hydraulic_requested": station.is_audio_layer_requested(unreal.Name("hydraulic_power")),
        "transfer_requested": station.is_audio_layer_requested(unreal.Name("transfer_servo")),
        "press_requested": station.is_audio_layer_requested(unreal.Name("press_phase")),
        "robot_requested": station.is_audio_layer_requested(unreal.Name("robot_servo")),
        "warning_requested": station.is_audio_layer_requested(unreal.Name("warning_alarm")),
        "last_cue": str(station.get_last_audio_cue_id()),
        "cue_sequence": station.get_audio_cue_sequence(),
        "components": component_rows(station),
    }


def finish(status, failure=None):
    global handle
    if failure: failures.append(failure)
    payload = {
        "$schema": "cairnwell/audit/press-train-a-audio-pie-v026/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": status if not failures else "FAIL__V026_TRAIN_A_AUDIO_PIE__NOT_PROMOTED",
        "map": MAP, "evidence": evidence, "failures": failures,
        "production_map_changed": False, "promotion_authorized": False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if failures: unreal.log_error(f"PRESS_TRAIN_A_AUDIO_V026_FAIL {failures}")
    else: unreal.log("PRESS_TRAIN_A_AUDIO_V026_PASS")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle); handle = None
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()


def tick(_delta):
    global phase, phase_started
    now = time.monotonic()
    if now - started > 25.0:
        finish("FAIL__V026_TRAIN_A_AUDIO_TIMEOUT__NOT_PROMOTED", f"timeout phase={phase}")
        return
    world = unreal.EditorLevelLibrary.get_game_world()
    if world is None: return
    stations = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBPressTrainAStation)
    if len(stations) != 1: return
    station = stations[0]

    if phase == "configure":
        if not station.has_complete_audio_asset_set():
            finish("FAIL__V026_TRAIN_A_AUDIO_ASSETS__NOT_PROMOTED", "native authority reports incomplete audio assets")
            return
        station.set_access_interlocks_closed(True)
        station.set_safety_circuit_healthy(True)
        station.set_emergency_stop_active(False)
        station.set_destack_healthy(True); station.set_transfer_healthy(True)
        station.set_hydraulic_pressure(280.0); station.set_press_load(45.0)
        station.set_inspection_healthy(True); station.set_stillage_output_clear(True)
        station.set_target_strokes_per_minute(15.0)
        for index in range(3):
            if not station.queue_reserved_blank(unreal.Name(f"PTA-AUDIO-RES-{index+1:03d}"),
                                                unreal.Name(f"PTA-AUDIO-BLANK-{index+1:03d}")):
                finish("FAIL__V026_TRAIN_A_AUDIO_INPUT__NOT_PROMOTED", f"blank {index+1} refused")
                return
        if not station.execute_remote_command(unreal.LBPressTrainACommand.POWER_ON, SOURCE, AUTHORITY):
            finish("FAIL__V026_TRAIN_A_AUDIO_POWER__NOT_PROMOTED", "power-on refused"); return
        if not station.execute_remote_command(unreal.LBPressTrainACommand.START, SOURCE, AUTHORITY):
            finish("FAIL__V026_TRAIN_A_AUDIO_START__NOT_PROMOTED", "start refused"); return
        phase = "wait_destack"; phase_started = now
        return

    snap = snapshot(station)
    if phase == "wait_destack" and now - phase_started >= 0.25:
        evidence["destack"] = snap
        loops = snap["components"]
        if not snap["hydraulic_requested"] or not snap["transfer_requested"]:
            finish("FAIL__V026_TRAIN_A_AUDIO_DESTACK_REQUEST__NOT_PROMOTED", f"destack={snap}"); return
        if not loops["PTA_Audio_HydraulicPower"]["is_playing"] or not loops["PTA_Audio_TransferServo"]["is_playing"]:
            finish("FAIL__V026_TRAIN_A_AUDIO_DESTACK_PLAYBACK__NOT_PROMOTED", f"destack={snap}"); return
        phase = "wait_press"; phase_started = now
        return

    if phase == "wait_press" and snap["press_requested"]:
        evidence["press"] = snap
        if snap["last_cue"] != "PTA_PressStroke_v001" or snap["cue_sequence"] < 1:
            finish("FAIL__V026_TRAIN_A_AUDIO_PRESS_CUE__NOT_PROMOTED", f"press={snap}"); return
        if not snap["components"]["PTA_Audio_PressCue"]["is_playing"]:
            finish("FAIL__V026_TRAIN_A_AUDIO_PRESS_PLAYBACK__NOT_PROMOTED", f"press={snap}"); return
        phase = "wait_robot"; phase_started = now
        return

    if phase == "wait_robot" and snap["robot_requested"]:
        evidence["robot"] = snap
        if not snap["components"]["PTA_Audio_RobotServo"]["is_playing"]:
            finish("FAIL__V026_TRAIN_A_AUDIO_ROBOT_PLAYBACK__NOT_PROMOTED", f"robot={snap}"); return
        station.request_controlled_stop()
        evidence["controlled_stop_command"] = snapshot(station)
        if str(station.get_last_audio_cue_id()) != "PTA_ControlledStop_v001":
            finish("FAIL__V026_TRAIN_A_AUDIO_STOP_CUE__NOT_PROMOTED", f"stop={evidence['controlled_stop_command']}"); return
        phase = "wait_ready"; phase_started = now
        return

    if phase == "wait_ready" and "READY" in snap["state"].upper():
        evidence["ready_after_stop"] = snap
        if snap["transfer_requested"] or snap["robot_requested"] or snap["warning_requested"]:
            finish("FAIL__V026_TRAIN_A_AUDIO_READY_LAYERS__NOT_PROMOTED", f"ready={snap}"); return
        if not station.execute_remote_command(unreal.LBPressTrainACommand.START, SOURCE, AUTHORITY):
            finish("FAIL__V026_TRAIN_A_AUDIO_RESTART__NOT_PROMOTED", "restart refused"); return
        station.set_access_interlocks_closed(False)
        phase = "wait_access_fault"; phase_started = now
        return

    if phase == "wait_access_fault" and now - phase_started >= 0.20 and "FAULT" in snap["state"].upper():
        evidence["access_fault"] = snap
        if not snap["warning_requested"] or snap["last_cue"] != "PTA_GateInterlock_v001":
            finish("FAIL__V026_TRAIN_A_AUDIO_ACCESS_FAULT__NOT_PROMOTED", f"fault={snap}"); return
        if not snap["components"]["PTA_Audio_WarningAlarm"]["is_playing"]:
            finish("FAIL__V026_TRAIN_A_AUDIO_ALARM_PLAYBACK__NOT_PROMOTED", f"fault={snap}"); return
        station.set_access_interlocks_closed(True)
        station.execute_remote_command(unreal.LBPressTrainACommand.ACKNOWLEDGE_ALARM, SOURCE, AUTHORITY)
        if not station.execute_remote_command(unreal.LBPressTrainACommand.RESET, SOURCE, AUTHORITY):
            finish("FAIL__V026_TRAIN_A_AUDIO_RESET__NOT_PROMOTED", "access fault reset refused"); return
        if not station.execute_remote_command(unreal.LBPressTrainACommand.START, SOURCE, AUTHORITY):
            finish("FAIL__V026_TRAIN_A_AUDIO_ESTOP_RESTART__NOT_PROMOTED", "restart before E-stop refused"); return
        station.set_emergency_stop_active(True)
        phase = "wait_estop"; phase_started = now
        return

    if phase == "wait_estop" and now - phase_started >= 0.12 and "FAULT" in snap["state"].upper():
        evidence["emergency_stop"] = snap
        if snap["last_cue"] != "PTA_EmergencyStop_v001" or not snap["warning_requested"]:
            finish("FAIL__V026_TRAIN_A_AUDIO_ESTOP_CUE__NOT_PROMOTED", f"estop={snap}"); return
        if not snap["components"]["PTA_Audio_SafetyCue"]["is_playing"]:
            finish("FAIL__V026_TRAIN_A_AUDIO_ESTOP_PLAYBACK__NOT_PROMOTED", f"estop={snap}"); return
        finish("PASS__V026_SPATIAL_HYDRAULIC_TRANSFER_PRESS_ROBOT_STOP_ACCESS_ESTOP_AND_ALARM_CAUSE_EFFECT__NOT_PROMOTED")


handle = unreal.register_slate_post_tick_callback(tick)
