"""Load the v198 campaign slot in a fresh editor process and prove safe restore/restart."""

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import unreal


unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR005AudioRuntimeCandidate_v198"
SLOT = "LB_AUTOMATION_PR005_V198_DISK_ROUNDTRIP"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/PressShopIntegration/press_shop_pr005_disk_slot_readback_v198.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
unreal.EditorLevelLibrary.editor_play_simulate()
started = time.monotonic()
phase = "load"
handle = None
records = []


def snapshot(station, label):
    status = station.get_hmi_status()
    row = {
        "label": label,
        "machine_state": str(status.machine_state),
        "active_fault": str(status.active_fault),
        "coil_id": status.coil_id,
        "recipe_id": str(status.recipe_id),
        "strip_length_m": status.strip_length_metres,
        "control_power": status.control_power_on,
        "guards_closed": status.guards_closed,
        "safety_healthy": status.safety_circuit_healthy,
        "certified": status.certified_for_production,
        "hpu_audio_requested": station.is_audio_layer_requested(unreal.Name("hpu_idle")),
    }
    records.append(row)
    return row


def finish(status, failure=None):
    global handle
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    deleted = unreal.GameplayStatics.delete_game_in_slot(SLOT, 0) if unreal.GameplayStatics.does_save_game_exist(SLOT, 0) else True
    absent = not unreal.GameplayStatics.does_save_game_exist(SLOT, 0)
    if not deleted or not absent:
        failure = (failure + "; " if failure else "") + "isolated automation slot cleanup failed"
        status = "RUNTIME_PR005_V198_DISK_READBACK_FAIL__NOT_PROMOTED"
    payload = {
        "$schema": "cairnwell/audit/press-shop-pr005-disk-slot-readback-v198/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "map": MAP,
        "slot": SLOT,
        "fresh_editor_process": True,
        "duration_seconds": time.monotonic() - started,
        "records": records,
        "slot_deleted_after_readback": deleted and absent,
        "failure": failure,
        "promotion_authorized": False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    if failure:
        unreal.log_error(f"LINE_BOSS_PR005_DISK_READBACK_V198_FAIL {failure}")
    else:
        unreal.log("LINE_BOSS_PR005_DISK_READBACK_V198_PASS")
    unreal.SystemLibrary.quit_editor()


def tick(_delta):
    global phase
    if time.monotonic() - started > 20.0:
        finish("RUNTIME_PR005_V198_DISK_READBACK_FAIL__NOT_PROMOTED", "timeout")
        return
    world = unreal.EditorLevelLibrary.get_game_world()
    if not world:
        return
    stations = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBPR005Station)
    if len(stations) != 1:
        return
    station = stations[0]
    if phase == "load":
        if not unreal.GameplayStatics.does_save_game_exist(SLOT, 0):
            finish("RUNTIME_PR005_V198_DISK_READBACK_FAIL__NOT_PROMOTED", "writer slot missing")
            return
        root = unreal.GameplayStatics.load_game_from_slot(SLOT, 0)
        if not root or root.get_editor_property("save_format_version") != 10:
            finish("RUNTIME_PR005_V198_DISK_READBACK_FAIL__NOT_PROMOTED", "campaign root load/format failed")
            return
        saved = root.get_editor_property("pr005")
        if not station.restore_save_state(saved):
            finish("RUNTIME_PR005_V198_DISK_READBACK_FAIL__NOT_PROMOTED", "station rejected disk state")
            return
        row = snapshot(station, "running_disk_snapshot_restored_safe")
        checks = [
            "IDLE" in row["machine_state"].upper(), row["coil_id"] == "MCX-U-CS10-0001",
            not row["safety_healthy"], row["certified"], row["hpu_audio_requested"],
        ]
        if not all(checks):
            finish("RUNTIME_PR005_V198_DISK_READBACK_FAIL__NOT_PROMOTED", f"safe restore checks={checks}")
            return
        station.set_guards_closed(True)
        station.set_safety_circuit_healthy(True)
        if not station.set_control_mode(unreal.LBPR005ControlMode.AUTOMATIC) or not station.press_cycle_start():
            finish("RUNTIME_PR005_V198_DISK_READBACK_FAIL__NOT_PROMOTED", "explicit restart rejected")
            return
        phase = "running"
        return
    if phase == "running" and "RUNNING" in str(station.get_machine_state()).upper():
        snapshot(station, "explicit_restart_after_disk_load")
        station.set_guards_closed(False)
        phase = "fault"
        return
    if phase == "fault" and "FAULT" in str(station.get_machine_state()).upper():
        row = snapshot(station, "guard_fault_after_disk_restart")
        checks = ["GATE_OR_INTERLOCK_OPEN" in row["active_fault"].upper(), station.is_audio_layer_requested(unreal.Name("warning_alarm"))]
        if not all(checks):
            finish("RUNTIME_PR005_V198_DISK_READBACK_FAIL__NOT_PROMOTED", f"fault checks={checks}")
            return
        finish("RUNTIME_PR005_V198_FRESH_PROCESS_CAMPAIGN_DISK_READBACK_SAFE_RESTART_AND_FAULT_PASS__NOT_PROMOTED")


handle = unreal.register_slate_post_tick_callback(tick)
