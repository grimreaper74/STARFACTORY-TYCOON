"""Exercise map-bound PR-008 native authority, movers, live HMI, stop and fault reset."""

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import unreal


unreal.EditorPythonScripting.set_keep_python_script_alive(True)
ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR008RuntimeCandidate_v060"
OUT = ROOT / "Saved/Audits/press_shop_pr008_runtime_v060.json"
EXPECTED_BINDINGS = {
    "LB_PR008_V058_PR008_FeedRollLower_01": "PR008_FeedRollLowerMover",
    "LB_PR008_V058_PR008_FeedRollUpper_01": "PR008_FeedRollUpperMover",
    "LB_PR008_V058_PR008_TelescopeBeam_01": "PR008_TelescopeMover",
    "LB_PR008_V058_PR008_TelescopeBeam_01_Drive": "PR008_TelescopeMover",
    "LB_PR008_V058_PR008_TelescopeBeam_02": "PR008_TelescopeMover",
    "LB_PR008_V058_PR008_TelescopeBeam_02_Drive": "PR008_TelescopeMover",
    "LB_PR008_V058_PR008_TelescopeBeam_03": "PR008_TelescopeMover",
    "LB_PR008_V058_PR008_TelescopeBeam_03_Drive": "PR008_TelescopeMover",
    "LB_PR008_V058_PR008_PressSlide": "PR008_PressSlideMover",
    "LB_PR008_V058_PR008_PrePunchDie": "PR008_PrePunchMover",
    "LB_PR008_V058_PR008_GuillotineBeam": "PR008_GuillotineMover",
    "LB_PR008_V058_PR008_OutfeedRoll_01": "PR008_OutfeedRollMover",
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
        "$schema": "line-boss/audit/press-shop-pr008-runtime-v060/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "map": MAP,
        "authority_count": 1 if initial is not None else 0,
        "binding_count": len(bindings),
        "bindings": bindings,
        "initial": initial,
        "running": running,
        "fault": fault,
        "save_format_version": 6,
        "automation_report": "Saved/Automation/PR008_Runtime_v001/index.json",
        "failure": failure,
        "promotion_authorized": False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if failure:
        unreal.log_error(f"LINE_BOSS_PR008_V060_RUNTIME_FAIL {failure}")
    else:
        unreal.log("LINE_BOSS_PR008_V060_RUNTIME_PASS")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()


def hmi_state_text(world):
    rows = [
        actor
        for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.TextRenderActor)
        if "PR008" in actor.get_actor_label().upper()
        and "HMI_TEXT_STATE" in actor.get_actor_label().upper()
    ]
    return str(rows[0].text_render.get_editor_property("text")) if len(rows) == 1 else ""


def tick(_delta_seconds):
    global phase, phase_started, initial, running, fault, bindings
    now = time.monotonic()
    if now - started > 45.0:
        finish("RUNTIME_PR008_NATIVE_FAIL__NOT_PROMOTED", f"timeout phase={phase}")
        return
    world = unreal.EditorLevelLibrary.get_game_world()
    if world is None:
        return
    stations = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBPR008Station)
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
            bindings.append(
                {"actor": label, "expected_parent": expected_parent, "actual_parent": actual_parent}
            )
        if any(row["actual_parent"] != row["expected_parent"] for row in bindings):
            finish("RUNTIME_PR008_NATIVE_FAIL__NOT_PROMOTED", "native mover binding mismatch")
            return
        initial = {
            "state": str(status.state),
            "strip_travel_metres": status.strip_travel_metres,
            "blanks_produced": status.blanks_produced,
            "scrap_bin_fill_percent": status.scrap_bin_fill_percent,
        }
        phase_started = now

    if phase == "wait_running":
        # The map begins in Threading for 1.5 s; sample only after enough
        # subsequent travel to complete at least one 1.55 m blank pitch.
        if "RUNNING" not in str(status.state).upper() or now - phase_started < 8.5:
            return
        text = hmi_state_text(world)
        running = {
            "state": str(status.state),
            "strip_travel_metres": status.strip_travel_metres,
            "blanks_produced": status.blanks_produced,
            "line_speed_metres_per_minute": status.line_speed_metres_per_minute,
            "hydraulic_pressure_bar": status.hydraulic_pressure_bar,
            "scrap_bin_fill_percent": status.scrap_bin_fill_percent,
            "cycle_progress": status.cycle_progress,
            "hmi_text": text,
        }
        checks = [
            status.strip_travel_metres > initial["strip_travel_metres"],
            status.blanks_produced > initial["blanks_produced"],
            status.scrap_bin_fill_percent > initial["scrap_bin_fill_percent"],
            status.line_speed_metres_per_minute > 0.0,
            "RUNNING" in text.upper(),
            "BLANKS" in text.upper(),
        ]
        if not all(checks):
            finish("RUNTIME_PR008_NATIVE_FAIL__NOT_PROMOTED", f"running checks={checks}")
            return
        station.request_controlled_stop()
        phase = "wait_ready"
        phase_started = now
        return

    if phase == "wait_ready":
        if "READY" not in str(status.state).upper():
            return
        if not station.start_line():
            finish("RUNTIME_PR008_NATIVE_FAIL__NOT_PROMOTED", "restart refused after controlled stop")
            return
        phase = "wait_restart_running"
        phase_started = now
        return

    if phase == "wait_restart_running":
        if "RUNNING" not in str(status.state).upper():
            return
        station.set_blank_outfeed_clear(False)
        phase = "wait_fault"
        phase_started = now
        return

    if phase == "wait_fault":
        if "FAULT" not in str(status.state).upper():
            return
        text = hmi_state_text(world)
        fault = {
            "state": str(status.state),
            "active_fault": str(status.active_fault),
            "hmi_text": text,
        }
        if "BLANKOUTFEEDBLOCKED" not in str(status.active_fault).upper().replace("_", "") or "FAULT" not in text.upper():
            finish("RUNTIME_PR008_NATIVE_FAIL__NOT_PROMOTED", "outfeed fault or live HMI mismatch")
            return
        station.set_blank_outfeed_clear(True)
        if not station.reset_fault():
            finish("RUNTIME_PR008_NATIVE_FAIL__NOT_PROMOTED", "corrected outfeed fault did not reset")
            return
        stable = station.capture_save_state()
        if "READY" not in str(stable.state).upper():
            finish("RUNTIME_PR008_NATIVE_FAIL__NOT_PROMOTED", "stable save was not Ready")
            return
        finish("RUNTIME_PR008_NATIVE_SEQUENCE_PASS__NOT_PROMOTED")


handle = unreal.register_slate_post_tick_callback(tick)
