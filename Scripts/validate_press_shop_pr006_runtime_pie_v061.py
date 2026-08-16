"""Exercise map-bound PR-006 calibration, motion bindings, live HMI and cassette fault reset."""

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import unreal


unreal.EditorPythonScripting.set_keep_python_script_alive(True)
ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR006RuntimeCandidate_v061"
OUT = ROOT / "Saved/Audits/press_shop_pr006_runtime_v061.json"
EXPECTED = {}
for index in range(1, 10):
    EXPECTED[f"LB_PR006_V054_PR006_LowerRoll_{index:02d}"] = f"PR006_LowerRollMover_{index:02d}"
for index in range(1, 11):
    EXPECTED[f"LB_PR006_V054_PR006_UpperRoll_{index:02d}"] = f"PR006_UpperRollMover_{index:02d}"
EXPECTED.update({
    "LB_PR006_V054_PR006_UpperCassette_Operator": "PR006_UpperCassetteMover",
    "LB_PR006_V054_PR006_UpperCassette_Drive": "PR006_UpperCassetteMover",
})
for index, suffix in enumerate(("-1_-1", "-1_+1", "+1_-1", "+1_+1"), 1):
    EXPECTED[f"LB_PR006_V054_PR006_GapCylinder_{suffix}"] = f"PR006_GapCylinderMover_{index:02d}"
for index in range(1, 4):
    EXPECTED[f"LB_PR006_V054_PR006_DriveMotor_{index:02d}"] = f"PR006_DriveMotorMover_{index:02d}"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
unreal.EditorLevelLibrary.editor_play_simulate()
started = time.monotonic()
phase_started = started
phase = "wait_running"
initial = None
running = None
fault = None
bindings = []
handle = None


def finish(status, failure=None):
    global handle
    payload = {
        "$schema": "line-boss/audit/press-shop-pr006-runtime-v061/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "map": MAP,
        "authority_count": 1 if initial is not None else 0,
        "binding_count": len(bindings),
        "bindings": bindings,
        "initial": initial,
        "running": running,
        "fault": fault,
        "save_format_version": 7,
        "automation_report": "Saved/Automation/PR006_Runtime_v001/index.json",
        "failure": failure,
        "promotion_authorized": False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if failure:
        unreal.log_error(f"LINE_BOSS_PR006_V061_RUNTIME_FAIL {failure}")
    else:
        unreal.log("LINE_BOSS_PR006_V061_RUNTIME_PASS")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()


def hmi_text(world):
    rows = [actor for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.TextRenderActor)
            if "PR006" in actor.get_actor_label().upper() and "HMI_TEXT_STATE" in actor.get_actor_label().upper()]
    return str(rows[0].text_render.get_editor_property("text")) if len(rows) == 1 else ""


def tick(_delta_seconds):
    global phase, phase_started, initial, running, fault, bindings
    now = time.monotonic()
    if now - started > 45.0:
        finish("RUNTIME_PR006_NATIVE_FAIL__NOT_PROMOTED", f"timeout phase={phase}")
        return
    world = unreal.EditorLevelLibrary.get_game_world()
    if world is None:
        return
    stations = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBPR006Station)
    if len(stations) != 1:
        return
    station = stations[0]
    status = station.get_hmi_status()

    if initial is None:
        all_actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
        by_label = {actor.get_actor_label(): actor for actor in all_actors}
        for label, expected_parent in EXPECTED.items():
            actor = by_label.get(label)
            root = actor.static_mesh_component if isinstance(actor, unreal.StaticMeshActor) else None
            parent = root.get_attach_parent() if root else None
            actual = parent.get_name() if parent else None
            bindings.append({"actor": label, "expected_parent": expected_parent, "actual_parent": actual})
        if any(row["actual_parent"] != row["expected_parent"] for row in bindings):
            finish("RUNTIME_PR006_NATIVE_FAIL__NOT_PROMOTED", "native mover binding mismatch")
            return
        initial = {
            "state": str(status.state), "actual_roll_gap_mm": status.actual_roll_gap_mm,
            "strip_travel_metres": status.strip_travel_metres, "motor_load_percent": status.motor_load_percent,
        }
        phase_started = now

    if phase == "wait_running":
        if "RUNNING" not in str(status.state).upper() or now - phase_started < 4.0:
            return
        text = hmi_text(world)
        running = {
            "state": str(status.state), "cassette_id": str(status.cassette_id),
            "actual_roll_gap_mm": status.actual_roll_gap_mm,
            "target_roll_gap_mm": status.target_roll_gap_mm,
            "strip_travel_metres": status.strip_travel_metres,
            "line_speed_metres_per_minute": status.line_speed_metres_per_minute,
            "motor_load_percent": status.motor_load_percent, "hmi_text": text,
        }
        checks = [
            abs(status.actual_roll_gap_mm - status.target_roll_gap_mm) <= 0.01,
            status.strip_travel_metres > initial["strip_travel_metres"],
            30.0 < status.motor_load_percent < 95.0,
            "RUNNING" in text.upper(), "GAP 1.15" in text.upper(),
        ]
        if not all(checks):
            finish("RUNTIME_PR006_NATIVE_FAIL__NOT_PROMOTED", f"running checks={checks}")
            return
        station.request_controlled_stop()
        phase = "wait_ready"
        phase_started = now
        return

    if phase == "wait_ready":
        if "READY" not in str(status.state).upper():
            return
        if not station.start_line():
            finish("RUNTIME_PR006_NATIVE_FAIL__NOT_PROMOTED", "restart refused after controlled stop")
            return
        phase = "wait_restart_running"
        phase_started = now
        return

    if phase == "wait_restart_running":
        if "RUNNING" not in str(status.state).upper():
            return
        station.set_cassette_locked(False)
        phase = "wait_fault"
        return

    if phase == "wait_fault":
        if "FAULT" not in str(status.state).upper():
            return
        text = hmi_text(world)
        fault = {"state": str(status.state), "active_fault": str(status.active_fault), "hmi_text": text}
        if "CASSETTEUNLOCKED" not in str(status.active_fault).upper().replace("_", "") or "FAULT" not in text.upper():
            finish("RUNTIME_PR006_NATIVE_FAIL__NOT_PROMOTED", "cassette fault or live HMI mismatch")
            return
        station.set_cassette_locked(True)
        if not station.reset_fault():
            finish("RUNTIME_PR006_NATIVE_FAIL__NOT_PROMOTED", "corrected cassette fault did not reset")
            return
        stable = station.capture_save_state()
        if "READY" not in str(stable.state).upper():
            finish("RUNTIME_PR006_NATIVE_FAIL__NOT_PROMOTED", "stable save was not Ready")
            return
        finish("RUNTIME_PR006_NATIVE_SEQUENCE_PASS__NOT_PROMOTED")


handle = unreal.register_slate_post_tick_callback(tick)
