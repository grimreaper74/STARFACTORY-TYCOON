"""PIE gate for PR005 state-requested spatial loops and cause-bound one-shots."""

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import unreal


unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR005AudioRuntimeCandidate_v198"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/PressShopIntegration/press_shop_pr005_audio_runtime_pie_v198.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
unreal.EditorLevelLibrary.editor_play_simulate()
started = time.monotonic()
phase = "setup"
phase_started = started
handle = None
station = None
records = []


def component_rows():
    result = {}
    for component in station.get_components_by_class(unreal.AudioComponent):
        sound = component.get_editor_property("sound")
        result[component.get_name()] = {
            "playing": bool(component.is_playing()),
            "sound": sound.get_name() if sound else None,
            "spatialized": bool(component.get_editor_property("allow_spatialization")),
            "attenuation_override": bool(component.get_editor_property("override_attenuation")),
        }
    return result


def requested():
    return {name: bool(station.is_audio_layer_requested(unreal.Name(name))) for name in (
        "hpu_idle", "coil_car_travel", "roller_drive", "strip_motion", "warning_alarm")}


def snapshot(label):
    row = {
        "label": label,
        "machine_state": str(station.get_machine_state()),
        "requested_layers": requested(),
        "last_audio_cue": str(station.get_last_audio_cue_id()),
        "audio_cue_sequence": station.get_audio_cue_sequence(),
        "components": component_rows(),
    }
    records.append(row)
    return row


def check_loops(row, expected):
    mapping = {
        "hpu_idle": "PR005_Audio_HPU",
        "coil_car_travel": "PR005_Audio_CoilCar",
        "roller_drive": "PR005_Audio_RollerDrive",
        "strip_motion": "PR005_Audio_StripMotion",
        "warning_alarm": "PR005_Audio_WarningAlarm",
    }
    failures = []
    for layer, wanted in expected.items():
        if row["requested_layers"].get(layer) != wanted:
            failures.append(f"{row['label']} {layer} requested={row['requested_layers'].get(layer)} expected={wanted}")
        component = row["components"].get(mapping[layer])
        if not component:
            failures.append(f"{row['label']} missing {mapping[layer]}")
        elif wanted and not component["playing"]:
            failures.append(f"{row['label']} {mapping[layer]} requested but not playing")
    return failures


def finish(failures):
    global handle
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    payload = {
        "$schema": "cairnwell/audit/press-shop-pr005-audio-runtime-pie-v198/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "RUNTIME_PR005_V198_STATE_DRIVEN_SPATIAL_AUDIO_PASS__NOT_PROMOTED" if not failures else "RUNTIME_PR005_V198_AUDIO_FAIL__NOT_PROMOTED",
        "map": MAP,
        "duration_seconds": time.monotonic() - started,
        "records": records,
        "failures": failures,
        "listening_note": "Playback activity is proven in PIE; final subjective mix/listening approval remains open.",
        "promotion_authorized": False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    if failures:
        unreal.log_error("LINE_BOSS_PR005_AUDIO_RUNTIME_V198_FAIL " + "; ".join(failures))
    else:
        unreal.log("LINE_BOSS_PR005_AUDIO_RUNTIME_V198_PASS")
    unreal.SystemLibrary.quit_editor()


failures = []


def tick(_delta):
    global station, phase, phase_started, failures
    now = time.monotonic()
    if now - started > 40.0:
        failures.append("timeout")
        finish(failures)
        return
    world = unreal.EditorLevelLibrary.get_game_world()
    if not world:
        return
    rows = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBPR005Station)
    if len(rows) != 1:
        return
    station = rows[0]

    if phase == "setup":
        station.set_control_power(True)
        station.set_utilities_available(True)
        station.load_coil_with_traceability("MCX-U-CS10-0001", "HT-CW26-08417", "LOT-MCXU-260804-A", "503184064100010", 1500.0)
        station.select_recipe(unreal.Name("U_SERIES_1500"), 1500.0)
        station.set_coil_car_positioned(True)
        station.set_mandrel_expanded(True)
        station.set_keeper_and_snubber(True, True)
        station.set_guards_closed(True)
        station.set_safety_circuit_healthy(True)
        station.set_strip_threaded(True)
        station.begin_commissioning()
        station.set_control_mode(unreal.LBPR005ControlMode.MANUAL)
        station.press_cycle_start()
        phase = "dry_cycle"
        phase_started = now
        return

    if phase == "dry_cycle" and now - phase_started > 0.6:
        row = snapshot("dry_cycle_motion")
        failures += check_loops(row, {"coil_car_travel": False, "roller_drive": True, "strip_motion": True, "hpu_idle": False, "warning_alarm": False})
        phase = "wait_first_off"
        return

    if phase == "wait_first_off" and "FIRST_OFF_VALIDATION" in str(station.get_machine_state()).upper():
        station.record_first_off_produced()
        station.approve_first_off()
        phase = "idle"
        phase_started = now
        return

    if phase == "idle" and now - phase_started > 0.5:
        row = snapshot("certified_idle")
        failures += check_loops(row, {"hpu_idle": True, "roller_drive": False, "strip_motion": False, "warning_alarm": False})
        station.set_control_mode(unreal.LBPR005ControlMode.AUTOMATIC)
        station.press_cycle_start()
        phase = "starting"
        phase_started = now
        return

    if phase == "starting" and now - phase_started > 0.4:
        row = snapshot("automatic_starting")
        failures += check_loops(row, {"hpu_idle": False, "roller_drive": False, "strip_motion": False, "warning_alarm": True})
        phase = "wait_running"
        return

    if phase == "wait_running" and "RUNNING" in str(station.get_machine_state()).upper():
        if now - phase_started < 2.5:
            return
        row = snapshot("automatic_running")
        failures += check_loops(row, {"hpu_idle": True, "roller_drive": True, "strip_motion": True, "warning_alarm": False})
        station.request_controlled_stop()
        phase = "stopping"
        phase_started = now
        return

    if phase == "stopping" and now - phase_started > 0.15:
        row = snapshot("controlled_stopping")
        cue = row["components"].get("PR005_Audio_ActuatorCue", {})
        if cue.get("sound") != "PR005_ControlledStop_v001" or "PR005_CONTROLLEDSTOP_V001" not in row["last_audio_cue"].upper():
            failures.append(f"controlled-stop cue not triggered: component={cue} last={row['last_audio_cue']}")
        phase = "wait_idle_again"
        return

    if phase == "wait_idle_again" and "IDLE" in str(station.get_machine_state()).upper():
        station.press_cycle_start()
        phase = "wait_fault_running"
        return

    if phase == "wait_fault_running" and "RUNNING" in str(station.get_machine_state()).upper():
        station.set_guards_closed(False)
        phase = "fault"
        phase_started = now
        return

    if phase == "fault" and now - phase_started > 0.12:
        row = snapshot("guard_open_fault")
        failures += check_loops(row, {"hpu_idle": False, "roller_drive": False, "strip_motion": False, "warning_alarm": True})
        cue = row["components"].get("PR005_Audio_SafetyCue", {})
        if cue.get("sound") != "PR005_EmergencyStop_v001" or "PR005_EMERGENCYSTOP_V001" not in row["last_audio_cue"].upper():
            failures.append(f"emergency-stop cue not triggered: component={cue} last={row['last_audio_cue']}")
        for name, component in row["components"].items():
            if not component["spatialized"] or not component["attenuation_override"]:
                failures.append(f"{name} missing spatial attenuation")
        finish(failures)


handle = unreal.register_slate_post_tick_callback(tick)
