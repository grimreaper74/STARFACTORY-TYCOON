"""Exact v197 PR005 commissioning, interlock, fault and save/restore PIE gate."""

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import unreal


unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR005RuntimeCageInfillCandidate_v197"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/PressShopIntegration/press_shop_pr005_runtime_sequence_v197.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
unreal.EditorLevelLibrary.editor_play_simulate()
started = time.monotonic()
phase_started = started
phase = "setup"
handle = None
station = None
records = []
running_save = None
fault_save = None


def state_name(value):
    return str(value)


def snapshot(label):
    status = station.get_hmi_status()
    row = {
        "label": label,
        "machine_state": state_name(status.machine_state),
        "active_fault": state_name(status.active_fault),
        "control_mode": state_name(status.control_mode),
        "coil_id": status.coil_id,
        "recipe_id": str(status.recipe_id),
        "coil_width_mm": status.coil_width_millimetres,
        "required_width_mm": status.required_width_millimetres,
        "strip_length_m": status.strip_length_metres,
        "cycle_count": status.cycle_count,
        "control_power": status.control_power_on,
        "utilities": status.utilities_available,
        "guards_closed": status.guards_closed,
        "safety_healthy": status.safety_circuit_healthy,
        "dry_cycle_complete": status.dry_cycle_complete,
        "quality_approved": status.quality_approved,
        "certified": status.certified_for_production,
        "can_dry_cycle": status.can_authorise_dry_cycle,
        "can_start_automatic": status.can_start_automatic,
        "blocking_reasons": [str(value) for value in status.blocking_reasons],
    }
    records.append(row)
    return row


def finish(status, failure=None):
    global handle
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    guard_rows = []
    world = unreal.EditorLevelLibrary.get_game_world()
    if world:
        for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.StaticMeshActor):
            label = actor.get_actor_label()
            if "GuardingHMI" not in label:
                continue
            component = actor.static_mesh_component
            guard_rows.append({
                "label": label,
                "collision": str(component.get_collision_enabled()),
                "profile": str(component.get_collision_profile_name()),
                "navigation": bool(component.get_editor_property("can_ever_affect_navigation")),
            })
    payload = {
        "$schema": "cairnwell/audit/press-shop-pr005-runtime-sequence-v197/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "map": MAP,
        "duration_seconds": time.monotonic() - started,
        "records": records,
        "native_guard_actors": guard_rows,
        "running_save_captured": running_save is not None,
        "fault_save_captured": fault_save is not None,
        "physical_gate_motion_authority": "OPEN__LOGICAL_INTERLOCK_PROVEN_PHYSICAL_GATE_ANIMATION_NOT_CLAIMED",
        "disk_slot_serialization": "OPEN__IN_MEMORY_VERSIONED_RESTORE_PROVEN_ONLY",
        "audio_binding": "OPEN__SOURCE_AUDIO_EXISTS_BUT_EXACT_V197_RUNTIME_BINDING_NOT_CLAIMED",
        "failure": failure,
        "promotion_authorized": False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if failure:
        unreal.log_error(f"LINE_BOSS_PR005_V197_SEQUENCE_FAIL phase={phase} failure={failure}")
    else:
        unreal.log("LINE_BOSS_PR005_V197_SEQUENCE_PASS")
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()


def tick(_delta):
    global station, phase, phase_started, running_save, fault_save
    now = time.monotonic()
    if now - started > 38.0:
        finish("RUNTIME_PR005_V197_SEQUENCE_FAIL__NOT_PROMOTED", "timeout")
        return
    world = unreal.EditorLevelLibrary.get_game_world()
    if world is None:
        return
    rows = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBPR005Station)
    if len(rows) != 1:
        return
    station = rows[0]
    status = station.get_hmi_status()

    if phase == "setup":
        station.set_control_power(True)
        station.set_utilities_available(True)
        loaded = station.load_coil_with_traceability("MCX-U-CS10-0001", "HT-CW26-08417", "LOT-MCXU-260804-A", "503184064100010", 1500.0)
        recipe = station.select_recipe(unreal.Name("U_SERIES_1500"), 1500.0)
        station.set_coil_car_positioned(True)
        station.set_mandrel_expanded(True)
        station.set_keeper_and_snubber(True, True)
        station.set_guards_closed(True)
        station.set_safety_circuit_healthy(True)
        station.set_strip_threaded(True)
        commissioned = station.begin_commissioning()
        manual = station.set_control_mode(unreal.LBPR005ControlMode.MANUAL)
        dry_started = station.press_cycle_start()
        row = snapshot("dry_cycle_started")
        checks = [loaded, recipe, commissioned, manual, dry_started, "DRY_CYCLE" in row["machine_state"].upper()]
        if not all(checks):
            finish("RUNTIME_PR005_V197_SEQUENCE_FAIL__NOT_PROMOTED", f"setup checks={checks}")
            return
        phase = "wait_first_off"
        phase_started = now
        return

    if phase == "wait_first_off":
        if "FIRST_OFF_VALIDATION" not in state_name(status.machine_state).upper():
            return
        station.record_first_off_produced()
        approved = station.approve_first_off()
        automatic = station.set_control_mode(unreal.LBPR005ControlMode.AUTOMATIC)
        auto_started = station.press_cycle_start()
        row = snapshot("automatic_starting")
        checks = [approved, automatic, auto_started, row["certified"], row["quality_approved"], "STARTING" in row["machine_state"].upper()]
        if not all(checks):
            finish("RUNTIME_PR005_V197_SEQUENCE_FAIL__NOT_PROMOTED", f"first-off checks={checks}")
            return
        phase = "wait_running"
        phase_started = now
        return

    if phase == "wait_running":
        if "RUNNING" not in state_name(status.machine_state).upper() or now - phase_started < 2.5:
            return
        running_save = station.capture_save_state()
        row = snapshot("running_before_interrupted_restore")
        if row["strip_length_m"] <= 0.0 or not station.restore_save_state(running_save):
            finish("RUNTIME_PR005_V197_SEQUENCE_FAIL__NOT_PROMOTED", "running capture/restore failed")
            return
        restored = snapshot("interrupted_motion_restored_safe")
        checks = [
            "IDLE" in restored["machine_state"].upper(),
            restored["coil_id"] == "MCX-U-CS10-0001",
            not restored["safety_healthy"],
            restored["certified"],
        ]
        if not all(checks):
            finish("RUNTIME_PR005_V197_SEQUENCE_FAIL__NOT_PROMOTED", f"interrupted restore checks={checks}")
            return
        station.set_guards_closed(True)
        station.set_safety_circuit_healthy(True)
        station.set_control_mode(unreal.LBPR005ControlMode.AUTOMATIC)
        if not station.press_cycle_start():
            finish("RUNTIME_PR005_V197_SEQUENCE_FAIL__NOT_PROMOTED", "restart refused after safe restore")
            return
        phase = "wait_restart_running"
        phase_started = now
        return

    if phase == "wait_restart_running":
        if "RUNNING" not in state_name(status.machine_state).upper():
            return
        station.set_guards_closed(False)
        phase = "wait_gate_fault"
        phase_started = now
        return

    if phase == "wait_gate_fault":
        status = station.get_hmi_status()
        if "FAULT" not in state_name(status.machine_state).upper():
            return
        fault_row = snapshot("gate_open_fault")
        if "GATE_OR_INTERLOCK_OPEN" not in fault_row["active_fault"].upper():
            finish("RUNTIME_PR005_V197_SEQUENCE_FAIL__NOT_PROMOTED", "wrong gate fault")
            return
        fault_save = station.capture_save_state()
        unsafe_open_reset = station.reset_fault()
        station.set_guards_closed(True)
        station.set_safety_circuit_healthy(False)
        unsafe_safety_reset = station.reset_fault()
        station.set_safety_circuit_healthy(True)
        safe_reset = station.reset_fault()
        reset_row = snapshot("corrected_gate_fault_reset")
        checks = [not unsafe_open_reset, not unsafe_safety_reset, safe_reset, "IDLE" in reset_row["machine_state"].upper()]
        if not all(checks):
            finish("RUNTIME_PR005_V197_SEQUENCE_FAIL__NOT_PROMOTED", f"fault reset checks={checks}")
            return
        if not station.restore_save_state(fault_save):
            finish("RUNTIME_PR005_V197_SEQUENCE_FAIL__NOT_PROMOTED", "fault save restore failed")
            return
        restored_fault = snapshot("fault_state_restored")
        checks = ["FAULT" in restored_fault["machine_state"].upper(), "GATE_OR_INTERLOCK_OPEN" in restored_fault["active_fault"].upper()]
        if not all(checks):
            finish("RUNTIME_PR005_V197_SEQUENCE_FAIL__NOT_PROMOTED", f"fault restore checks={checks}")
            return
        station.set_guards_closed(True)
        station.set_safety_circuit_healthy(True)
        if not station.reset_fault():
            finish("RUNTIME_PR005_V197_SEQUENCE_FAIL__NOT_PROMOTED", "restored fault final reset failed")
            return
        snapshot("final_stable_idle")
        finish("RUNTIME_PR005_V197_COMMISSIONING_INTERLOCK_FAULT_AND_IN_MEMORY_SAVE_RESTORE_PASS__NOT_PROMOTED")


handle = unreal.register_slate_post_tick_callback(tick)
