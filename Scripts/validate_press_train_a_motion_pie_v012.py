"""Exercise Train A v012 motion bindings, state feedback, safety and isolation in PIE."""

import json
import math
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import unreal


unreal.EditorPythonScripting.set_keep_python_script_alive(True)
ROOT = Path(unreal.Paths.project_dir())
MAP = os.environ.get("LB_PTA_VALIDATION_MAP", "/Game/LineBoss/Maps/LB_PressTrainAMotionCandidate_v012")
OUTPUT_RELATIVE = os.environ.get(
    "LB_PTA_VALIDATION_OUTPUT", "Saved/Audits/PressTrains/press_train_a_motion_pie_v012.json")
OUT = ROOT / OUTPUT_RELATIVE
VALIDATION_LABEL = os.environ.get("LB_PTA_VALIDATION_LABEL", "V012").upper()
AUTHORITY = unreal.Name("CW.MW.CONTROL_ROOM")
SOURCE = unreal.Name("MW.MCR.TRAIN_A.CONSOLE")

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
unreal.EditorLevelLibrary.editor_play_simulate()
started = time.monotonic()
phase_started = started
phase = "configure"
initial = None
running = None
stopped = None
fault = None
isolation = None
motion = {
    "destack_cm": 0.0, "transfer_cm": 0.0, "slide_cm": 0.0, "upper_die_cm": 0.0,
    "robot_deg": 0.0, "panel_cm": 0.0, "workpiece_visible_max": 0,
    "green_beacons_visible_max": 0, "amber_beacons_visible_max": 0, "red_beacons_visible_max": 0,
}
baseline = {}
handle = None


def vec(value):
    return [value.x, value.y, value.z]


def rot(value):
    return [value.pitch, value.yaw, value.roll]


def angular_delta(a, b):
    return max(abs((x - y + 180.0) % 360.0 - 180.0) for x, y in zip(a, b))


def tagged(actors, tag):
    return [actor for actor in actors if unreal.Name(tag) in actor.tags]


def is_visible(actor):
    try:
        return not actor.is_hidden()
    except Exception:
        return not bool(actor.get_editor_property("hidden"))


def hmi_text(world):
    rows = [actor for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.TextRenderActor)
            if unreal.Name("LB.HMI.PressTrainA.LiveState") in actor.tags]
    return str(rows[0].text_render.get_editor_property("text")) if len(rows) == 1 else ""


def finish(status, failure=None):
    global handle
    status = status.replace("V012", VALIDATION_LABEL)
    payload = {
        "$schema": f"cairnwell/audit/press-train-a-motion-pie-{VALIDATION_LABEL.lower()}/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "map": MAP,
        "initial": initial,
        "running": running,
        "controlled_stop": stopped,
        "fault_recovery": fault,
        "isolation": isolation,
        "motion_maxima": motion,
        "save_root_format": 11,
        "train_save_version": 1,
        "automation_test": "LineBoss.PressShop.PressTrains.TrainA.RuntimeSafetySave",
        "failure": failure,
        "world_placement": "TBC_NOT_INVENTED",
        "promotion_authorized": False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if failure:
        unreal.log_error(f"PRESS_TRAIN_A_MOTION_{VALIDATION_LABEL}_FAIL {failure}")
    else:
        unreal.log(f"PRESS_TRAIN_A_MOTION_{VALIDATION_LABEL}_PASS")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()


def tick(_delta):
    global phase, phase_started, initial, running, stopped, fault, isolation
    now = time.monotonic()
    if now - started > 48.0:
        finish("FAIL__V012_MOTION_PIE_TIMEOUT__NOT_PROMOTED", f"timeout phase={phase}")
        return
    world = unreal.EditorLevelLibrary.get_game_world()
    if world is None:
        return
    stations = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBPressTrainAStation)
    if len(stations) != 1:
        return
    station = stations[0]
    all_actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
    groups = {
        "destack": tagged(all_actors, "LB.PressTrain.Role.destack_lift"),
        "transfer": tagged(all_actors, "LB.PressTrain.Role.transfer_crossbar"),
        "slide": tagged(all_actors, "LB.PressTrain.Role.moving_press_slide"),
        "upper_die": tagged(all_actors, "LB.PressTrain.Role.moving_upper_die"),
        "workpiece": tagged(all_actors, "LB.PressTrain.Role.carried_workpiece_state"),
        "robot": tagged(all_actors, "LB.PressTrain.Role.unload_robot_shoulder_runtime"),
        "panel": tagged(all_actors, "LB.PressTrain.Role.visible_formed_panel"),
        "red": tagged(all_actors, "LB.PressTrain.Role.state_beacon_red"),
        "amber": tagged(all_actors, "LB.PressTrain.Role.state_beacon_amber"),
        "green": tagged(all_actors, "LB.PressTrain.Role.state_beacon_green"),
    }

    if phase == "configure":
        if any(not group for group in groups.values()):
            finish("FAIL__V012_MOTION_PIE_BINDINGS__NOT_PROMOTED", "required tagged presentation group missing")
            return
        exact_counts = {"slide": 5, "upper_die": 5, "workpiece": 5, "robot": 1, "red": 5, "amber": 5, "green": 5}
        actual_counts = {key: len(groups[key]) for key in exact_counts}
        if actual_counts != exact_counts:
            finish("FAIL__V012_MOTION_PIE_EXACT_BINDING_COUNTS__NOT_PROMOTED", f"counts={actual_counts}")
            return
        for key, group in groups.items():
            baseline[key] = [(vec(actor.get_actor_location()), rot(actor.get_actor_rotation())) for actor in group]
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
        if not station.queue_reserved_blank(unreal.Name("PTA-PIE-RES-001"), unreal.Name("PR010-BLANK-PIE-001")):
            finish("FAIL__V012_MOTION_PIE_INPUT__NOT_PROMOTED", "first reserved blank refused")
            return
        if not station.queue_reserved_blank(unreal.Name("PTA-PIE-RES-002"), unreal.Name("PR010-BLANK-PIE-002")):
            finish("FAIL__V012_MOTION_PIE_INPUT__NOT_PROMOTED", "second reserved blank refused")
            return
        if station.execute_remote_command(unreal.LBPressTrainACommand.START, SOURCE, unreal.Name("UNTRUSTED")):
            finish("FAIL__V012_MOTION_PIE_AUTHORITY__NOT_PROMOTED", "untrusted start accepted")
            return
        if not station.execute_remote_command(unreal.LBPressTrainACommand.POWER_ON, SOURCE, AUTHORITY):
            finish("FAIL__V012_MOTION_PIE_POWER__NOT_PROMOTED", "authorised power-on refused")
            return
        if not station.execute_remote_command(unreal.LBPressTrainACommand.START, SOURCE, AUTHORITY):
            finish("FAIL__V012_MOTION_PIE_START__NOT_PROMOTED", "authorised start refused")
            return
        status = station.get_hmi_status()
        initial = {"state": str(status.state), "phase": str(status.phase),
                   "pending_blanks": status.pending_blank_count, "in_process_blank": str(status.process_blank_id)}
        phase = "wait_cycle"
        phase_started = now
        return

    for key, group in groups.items():
        for index, actor in enumerate(group):
            base_loc, base_rot = baseline[key][index]
            loc_delta = math.dist(vec(actor.get_actor_location()), base_loc)
            rot_delta = angular_delta(rot(actor.get_actor_rotation()), base_rot)
            if key == "destack": motion["destack_cm"] = max(motion["destack_cm"], loc_delta)
            elif key == "transfer": motion["transfer_cm"] = max(motion["transfer_cm"], loc_delta)
            elif key == "slide": motion["slide_cm"] = max(motion["slide_cm"], loc_delta)
            elif key == "upper_die": motion["upper_die_cm"] = max(motion["upper_die_cm"], loc_delta)
            elif key == "robot": motion["robot_deg"] = max(motion["robot_deg"], rot_delta)
            elif key == "panel": motion["panel_cm"] = max(motion["panel_cm"], loc_delta)
    motion["workpiece_visible_max"] = max(motion["workpiece_visible_max"], sum(is_visible(actor) for actor in groups["workpiece"]))
    motion["green_beacons_visible_max"] = max(motion["green_beacons_visible_max"], sum(is_visible(actor) for actor in groups["green"]))
    motion["amber_beacons_visible_max"] = max(motion["amber_beacons_visible_max"], sum(is_visible(actor) for actor in groups["amber"]))
    motion["red_beacons_visible_max"] = max(motion["red_beacons_visible_max"], sum(is_visible(actor) for actor in groups["red"]))

    status = station.get_hmi_status()
    if phase == "wait_cycle":
        if status.good_panels < 1:
            return
        text = hmi_text(world)
        running = {"state": str(status.state), "phase": str(status.phase), "good_panels": status.good_panels,
                   "pending_panels": status.pending_panel_count, "hmi_text": text}
        checks = (motion["destack_cm"] > 10.0 and motion["transfer_cm"] > 100.0
                  and motion["slide_cm"] > 20.0 and motion["upper_die_cm"] > 20.0
                  and motion["robot_deg"] > 5.0 and motion["panel_cm"] > 20.0
                  and motion["workpiece_visible_max"] >= 1 and motion["green_beacons_visible_max"] == 5
                  and "TRAIN A" in text.upper() and status.pending_panel_count >= 1)
        if not checks:
            finish("FAIL__V012_MOTION_PIE_MOTION_HMI__NOT_PROMOTED", f"motion={motion} text={text}")
            return
        station.request_controlled_stop()
        phase = "wait_stop"
        phase_started = now
        return

    if phase == "wait_stop":
        if "READY" not in str(status.state).upper():
            return
        stopped = {"state": str(status.state), "cycle_progress": status.cycle_progress,
                   "in_process_blank": str(status.process_blank_id)}
        if status.process_blank_id == unreal.Name("None"):
            finish("FAIL__V012_MOTION_PIE_STOP_IDENTITY__NOT_PROMOTED", "controlled stop lost in-process identity")
            return
        if sum(is_visible(actor) for actor in groups["amber"]) != 5:
            finish("FAIL__V012_MOTION_PIE_READY_BEACONS__NOT_PROMOTED", "amber ready beacons not visible")
            return
        if not station.execute_remote_command(unreal.LBPressTrainACommand.START, SOURCE, AUTHORITY):
            finish("FAIL__V012_MOTION_PIE_RESTART__NOT_PROMOTED", "restart after controlled stop refused")
            return
        station.set_access_interlocks_closed(False)
        phase = "wait_fault"
        phase_started = now
        return

    if phase == "wait_fault":
        if "FAULT" not in str(status.state).upper():
            return
        if sum(is_visible(actor) for actor in groups["red"]) != 5:
            finish("FAIL__V012_MOTION_PIE_FAULT_BEACONS__NOT_PROMOTED", "red fault beacons not visible")
            return
        station.set_access_interlocks_closed(True)
        reset_without_ack = station.reset_fault()
        ack = station.execute_remote_command(unreal.LBPressTrainACommand.ACKNOWLEDGE_ALARM, SOURCE, AUTHORITY)
        reset = station.execute_remote_command(unreal.LBPressTrainACommand.RESET, SOURCE, AUTHORITY)
        fault = {"fault": str(status.active_fault), "reset_without_ack": reset_without_ack,
                 "acknowledged": ack, "reset_after_correction": reset}
        if reset_without_ack or not ack or not reset:
            finish("FAIL__V012_MOTION_PIE_FAULT_RECOVERY__NOT_PROMOTED", f"fault={fault}")
            return
        if not station.execute_remote_command(unreal.LBPressTrainACommand.REQUEST_ISOLATION, SOURCE, AUTHORITY):
            finish("FAIL__V012_MOTION_PIE_ISOLATION_REQUEST__NOT_PROMOTED", "isolation request refused")
            return
        phase = "wait_isolated"
        phase_started = now
        return

    if phase == "wait_isolated":
        if "ISOLATED" not in str(status.state).upper():
            return
        missing_evidence = station.confirm_zero_energy_isolation(True, True, unreal.Name("None"))
        proof = station.confirm_zero_energy_isolation(True, True, unreal.Name("PTA-ZEP-PIE-001"))
        release = station.execute_remote_command(unreal.LBPressTrainACommand.RELEASE_ISOLATION, SOURCE, AUTHORITY)
        saved = station.capture_save_state()
        after = station.get_hmi_status()
        isolation = {"missing_evidence_accepted": missing_evidence, "proof_accepted": proof,
                     "release_accepted": release, "state_after_release": str(after.state),
                     "evidence_id": str(after.last_safety_evidence_id), "save_version": saved.version}
        if missing_evidence or not proof or not release or saved.version != 1 or "READY" not in str(after.state).upper():
            finish("FAIL__V012_MOTION_PIE_ISOLATION__NOT_PROMOTED", f"isolation={isolation}")
            return
        finish("PASS__V012_NATIVE_SLIDES_DIES_WORKPIECE_ROBOT_BEACONS_HMI_CONTROLLED_STOP_FAULT_ISOLATION_SAVE_GATE__NOT_PROMOTED")


handle = unreal.register_slate_post_tick_callback(tick)
