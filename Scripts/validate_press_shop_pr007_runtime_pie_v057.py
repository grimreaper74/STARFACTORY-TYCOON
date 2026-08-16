"""Exercise the map-bound native PR-007 authority in PIE and write a durable audit."""
import json
import time
from datetime import datetime, timezone
from pathlib import Path
import unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR007RuntimeCandidate_v057"
OUT = ROOT / "Saved/Audits/press_shop_pr007_runtime_v057.json"
EXPECTED_BINDINGS = {
    "LB_PR007_V055_PR007_HoodWash": "PR007_WashHoodMover",
    "LB_PR007_V055_PR007_WashPumpMotor": "PR007_WashPumpMover",
    "LB_PR007_V055_PR007_LubePumpMotor": "PR007_LubePumpMover",
    "LB_PR007_V055_PR007_InfeedRollLower": "PR007_FeedRollerMover",
    "LB_PR007_V055_PR007_WashRollLower": "PR007_WashRollerMover",
    "LB_PR007_V055_PR007_LubeRollLower": "PR007_LubeRollerMover",
    "LB_PR007_V055_PR007_OutfeedRollLower": "PR007_OutfeedRollerMover",
}

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
        "$schema": "line-boss/audit/press-shop-pr007-runtime-v057/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "map": MAP,
        "authority_count": 1 if initial is not None else 0,
        "binding_count": len(bindings),
        "bindings": bindings,
        "initial": initial,
        "running": running,
        "fault": fault,
        "failure": failure,
        "promotion_authorized": False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if failure:
        unreal.log_error(f"LINE_BOSS_PR007_V057_RUNTIME_FAIL {failure}")
    else:
        unreal.log("LINE_BOSS_PR007_V057_RUNTIME_PASS")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()

def tick(_delta_seconds):
    global phase, phase_started, initial, running, fault, bindings
    now = time.monotonic()
    if now - started > 35.0:
        finish("RUNTIME_PR007_NATIVE_FAIL__NOT_PROMOTED", f"timeout phase={phase}")
        return
    world = unreal.EditorLevelLibrary.get_game_world()
    if world is None:
        return
    stations = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBPR007Station)
    if len(stations) != 1:
        return
    station = stations[0]
    status = station.get_hmi_status()

    if initial is None:
        all_actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
        by_label = {actor.get_actor_label(): actor for actor in all_actors}
        for label, expected_parent in EXPECTED_BINDINGS.items():
            actor = by_label.get(label)
            root_component = actor.static_mesh_component if isinstance(actor, unreal.StaticMeshActor) else None
            parent = root_component.get_attach_parent() if root_component else None
            actual_parent = parent.get_name() if parent else None
            bindings.append({"actor": label, "expected_parent": expected_parent, "actual_parent": actual_parent})
        if any(row["actual_parent"] != row["expected_parent"] for row in bindings):
            finish("RUNTIME_PR007_NATIVE_FAIL__NOT_PROMOTED", "native mover binding mismatch")
            return
        initial = {
            "state": str(status.state),
            "wash_level_percent": status.wash_level_percent,
            "lube_level_percent": status.lube_level_percent,
            "strip_travel_metres": status.strip_travel_metres,
        }
        phase_started = now

    if phase == "wait_running":
        if "RUNNING" not in str(status.state).upper():
            return
        if now - phase_started < 1.0:
            return
        hmi_rows = [actor for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.TextRenderActor)
                    if "PR007" in actor.get_actor_label().upper() and "HMI_TEXT_STATE" in actor.get_actor_label().upper()]
        hmi_text = str(hmi_rows[0].text_render.get_editor_property("text")) if len(hmi_rows) == 1 else ""
        running = {
            "state": str(status.state),
            "wash_level_percent": status.wash_level_percent,
            "lube_level_percent": status.lube_level_percent,
            "strip_travel_metres": status.strip_travel_metres,
            "line_speed_metres_per_minute": status.line_speed_metres_per_minute,
            "hood_position": status.hood_position,
            "hmi_text": hmi_text,
        }
        checks = [
            status.strip_travel_metres > initial["strip_travel_metres"],
            status.wash_level_percent < initial["wash_level_percent"],
            status.lube_level_percent < initial["lube_level_percent"],
            status.hood_position > 0.99,
            "RUNNING" in hmi_text.upper(),
        ]
        if not all(checks):
            finish("RUNTIME_PR007_NATIVE_FAIL__NOT_PROMOTED", f"running checks={checks}")
            return
        station.request_controlled_stop()
        phase = "wait_ready"
        phase_started = now
        return

    if phase == "wait_ready":
        if "READY" not in str(status.state).upper():
            return
        if not station.start_line():
            finish("RUNTIME_PR007_NATIVE_FAIL__NOT_PROMOTED", "restart refused after controlled stop")
            return
        phase = "wait_restart_running"
        phase_started = now
        return

    if phase == "wait_restart_running":
        if "RUNNING" not in str(status.state).upper():
            return
        station.set_guards_closed(False)
        phase = "wait_fault"
        phase_started = now
        return

    if phase == "wait_fault":
        if "FAULT" not in str(status.state).upper():
            return
        hmi_rows = [actor for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.TextRenderActor)
                    if "PR007" in actor.get_actor_label().upper() and "HMI_TEXT_STATE" in actor.get_actor_label().upper()]
        hmi_text = str(hmi_rows[0].text_render.get_editor_property("text")) if len(hmi_rows) == 1 else ""
        fault = {"state": str(status.state), "active_fault": str(status.active_fault), "hmi_text": hmi_text}
        if "GUARDOPEN" not in str(status.active_fault).upper().replace("_", "") or "FAULT" not in hmi_text.upper():
            finish("RUNTIME_PR007_NATIVE_FAIL__NOT_PROMOTED", "guard fault or HMI fault presentation mismatch")
            return
        station.set_guards_closed(True)
        if not station.reset_fault():
            finish("RUNTIME_PR007_NATIVE_FAIL__NOT_PROMOTED", "corrected guard fault did not reset")
            return
        stable = station.capture_save_state()
        if "READY" not in str(stable.state).upper():
            finish("RUNTIME_PR007_NATIVE_FAIL__NOT_PROMOTED", "stable save was not Ready")
            return
        finish("RUNTIME_PR007_NATIVE_SEQUENCE_PASS__NOT_PROMOTED")

handle = unreal.register_slate_post_tick_callback(tick)
