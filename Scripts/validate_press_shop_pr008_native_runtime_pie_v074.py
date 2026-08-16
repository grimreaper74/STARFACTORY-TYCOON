"""Exercise detailed v074 PR-008 bindings, motion, HMI, safety and isolation in PIE."""

import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path

import unreal


unreal.EditorPythonScripting.set_keep_python_script_alive(True)
ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR008NativeRuntimeCandidate_v074"
OUT = ROOT / "Saved/Audits/press_shop_pr008_native_runtime_v074.json"
AUTHORITY = unreal.Name("CW.MW.CONTROL_ROOM")
SOURCE = unreal.Name("MW.MCR.PR008.CONSOLE")

ATTACHED_BINDINGS = {
    "LB_PR008_V066_SM_CA_MW_PR008_ServoFeedRoll_Lower_01": "PR008_FeedRollLowerMover",
    "LB_PR008_V066_SM_CA_MW_PR008_ServoFeedSleeve_Lower_01": "PR008_FeedRollLowerMover",
    "LB_PR008_V066_SM_CA_MW_PR008_ServoFeedRoll_Upper_01": "PR008_FeedRollUpperMover",
    "LB_PR008_V066_SM_CA_MW_PR008_ServoFeedSleeve_Upper_01": "PR008_FeedRollUpperMover",
    "LB_PR008_V065_SM_CA_MW_PR008_EdgeGuide_Operator": "PR008_EdgeGuideOperatorMover",
    "LB_PR008_V065_SM_CA_MW_PR008_EdgeGuide_Drive": "PR008_EdgeGuideDriveMover",
    "LB_PR008_V067_SM_CA_MW_PR008_TelescopeStage1_01": "PR008_TelescopeStage1Mover",
    "LB_PR008_V067_SM_CA_MW_PR008_TelescopeStage2_01": "PR008_TelescopeStage2Mover",
    "LB_PR008_V067_SM_CA_MW_PR008_TelescopeStage3_01": "PR008_TelescopeStage3Mover",
    "LB_PR008_V068_SM_CA_MW_PR008_PrePunchSlide_01": "PR008_PrePunchMover",
    "LB_PR008_V068_SM_CA_MW_PR008_PrePunchScrapFlap_01": "PR008_ScrapFlapMover",
    "LB_PR008_V068_SM_CA_MW_PR008_PrePunchServiceDoor_Operator": "PR008_ServiceDoorOperatorMover",
    "LB_PR008_V068_SM_CA_MW_PR008_PrePunchServiceDoor_Drive": "PR008_ServiceDoorDriveMover",
    "LB_PR008_V069_SM_CA_MW_PR008_ShearBladeBeam_01": "PR008_GuillotineMover",
}
MOTION_ACTORS = {
    "feed_lower": "LB_PR008_V066_SM_CA_MW_PR008_ServoFeedRoll_Lower_01",
    "loop_roll": "LB_PR008_V064_SM_CA_MW_PR008_LoopRoll_01",
    "edge_guide": "LB_PR008_V065_SM_CA_MW_PR008_EdgeGuide_Operator",
    "telescope_tip": "LB_PR008_V067_SM_CA_MW_PR008_TelescopeStage3_01",
    "pre_punch": "LB_PR008_V068_SM_CA_MW_PR008_PrePunchSlide_01",
    "scrap_flap": "LB_PR008_V068_SM_CA_MW_PR008_PrePunchScrapFlap_01",
    "shear": "LB_PR008_V069_SM_CA_MW_PR008_ShearBladeBeam_01",
    "discharge_roll": "LB_PR008_V070_SM_CA_MW_PR008_DischargeRoll_01",
}

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
unreal.EditorLevelLibrary.editor_play_simulate()
started = time.monotonic()
phase_started = started
phase = "wait_running"
initial_status = None
running_status = None
fault_status = None
isolation_status = None
bindings = []
interaction_checks = []
initial_transforms = {}
max_location_delta = {key: 0.0 for key in MOTION_ACTORS}
max_rotation_delta = {key: 0.0 for key in MOTION_ACTORS}
edge_commanded = False
handle = None


def vector_tuple(value):
    return [value.x, value.y, value.z]


def rotation_tuple(value):
    return [value.pitch, value.yaw, value.roll]


def angular_delta(a, b):
    return max(abs((x - y + 180.0) % 360.0 - 180.0) for x, y in zip(a, b))


def hmi_state_text(world):
    rows = [actor for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.TextRenderActor)
            if unreal.Name("LB.HMI.PR008.LiveState") in actor.tags]
    return str(rows[0].text_render.get_editor_property("text")) if len(rows) == 1 else ""


def finish(status, failure=None):
    global handle
    payload = {
        "$schema": "line-boss/audit/press-shop-pr008-native-runtime-v074/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "map": MAP,
        "authority_count": 1 if initial_status is not None else 0,
        "attached_binding_count": len(bindings),
        "attached_bindings": bindings,
        "interaction_checks": interaction_checks,
        "initial": initial_status,
        "running": running_status,
        "fault": fault_status,
        "isolation": isolation_status,
        "motion_max_location_delta_cm": max_location_delta,
        "motion_max_rotation_delta_degrees": max_rotation_delta,
        "save_root_format": 7,
        "station_save_version": 2,
        "automation_report": "Saved/Automation/PR008_Runtime_v002/index.json",
        "failure": failure,
        "promotion_authorized": False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if failure:
        unreal.log_error(f"LINE_BOSS_PR008_V074_RUNTIME_FAIL {failure}")
    else:
        unreal.log("LINE_BOSS_PR008_V074_RUNTIME_PASS")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()


def tick(_delta_seconds):
    global phase, phase_started, initial_status, running_status, fault_status
    global isolation_status, bindings, interaction_checks, edge_commanded
    now = time.monotonic()
    if now - started > 55.0:
        finish("RUNTIME_PR008_V074_FAIL__NOT_PROMOTED", f"timeout phase={phase}")
        return
    world = unreal.EditorLevelLibrary.get_game_world()
    if world is None:
        return
    stations = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBPR008Station)
    if len(stations) != 1:
        return
    station = stations[0]
    status = station.get_hmi_status()
    all_actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
    by_label = {actor.get_actor_label(): actor for actor in all_actors}

    if initial_status is None:
        for label, expected_parent in ATTACHED_BINDINGS.items():
            actor = by_label.get(label)
            root = actor.static_mesh_component if isinstance(actor, unreal.StaticMeshActor) else None
            parent = root.get_attach_parent() if root else None
            bindings.append({"actor": label, "expected_parent": expected_parent,
                             "actual_parent": parent.get_name() if parent else None})
        if any(row["actual_parent"] != row["expected_parent"] for row in bindings):
            finish("RUNTIME_PR008_V074_FAIL__NOT_PROMOTED", "native attached-binding mismatch")
            return
        for contract in ("LB.HMI.PR008.TouchSurface", "LB.HMI.PR008.LocalControls", "LB.HMI.PR008.EStop"):
            matches = [actor for actor in all_actors if unreal.Name(contract) in actor.tags]
            collision = None
            if len(matches) == 1 and isinstance(matches[0], unreal.StaticMeshActor):
                collision = str(matches[0].static_mesh_component.get_collision_enabled())
            interaction_checks.append({"contract": contract, "count": len(matches), "collision": collision})
        if any(row["count"] != 1 or "NO_COLLISION" in (row["collision"] or "").upper()
               for row in interaction_checks):
            finish("RUNTIME_PR008_V074_FAIL__NOT_PROMOTED", "HMI interaction contract mismatch")
            return
        for key, label in MOTION_ACTORS.items():
            actor = by_label.get(label)
            if actor is None:
                finish("RUNTIME_PR008_V074_FAIL__NOT_PROMOTED", f"missing motion actor {label}")
                return
            initial_transforms[key] = {
                "location": vector_tuple(actor.get_actor_location()),
                "rotation": rotation_tuple(actor.get_actor_rotation()),
            }
        initial_status = {
            "state": str(status.state), "runtime_phase": str(status.runtime_phase),
            "strip_travel_metres": status.strip_travel_metres,
            "blanks_produced": status.blanks_produced,
            "last_command_source": str(status.last_command_source),
        }
        if station.execute_remote_command(unreal.LBPR008Command.START, SOURCE, unreal.Name("UNTRUSTED")):
            finish("RUNTIME_PR008_V074_FAIL__NOT_PROMOTED", "untrusted remote authority accepted")
            return
        phase_started = now

    for key, label in MOTION_ACTORS.items():
        actor = by_label[label]
        loc = vector_tuple(actor.get_actor_location())
        rot = rotation_tuple(actor.get_actor_rotation())
        base = initial_transforms[key]
        max_location_delta[key] = max(max_location_delta[key], math.dist(loc, base["location"]))
        max_rotation_delta[key] = max(max_rotation_delta[key], angular_delta(rot, base["rotation"]))

    if phase == "wait_running":
        if "RUNNING" not in str(status.state).upper():
            return
        if not edge_commanded:
            station.set_edge_tracking_deviation(100.0)
            edge_commanded = True
        if now - phase_started < 10.5:
            return
        station.set_edge_tracking_deviation(0.0)
        text = hmi_state_text(world)
        running_status = {
            "state": str(status.state), "runtime_phase": str(status.runtime_phase),
            "strip_travel_metres": status.strip_travel_metres,
            "blanks_produced": status.blanks_produced,
            "line_speed_metres_per_minute": status.line_speed_metres_per_minute,
            "cycle_progress": status.cycle_progress, "hmi_text": text,
        }
        motion_checks = {
            "feed_lower_rotation": max_rotation_delta["feed_lower"] > 5.0,
            "loop_roll_rotation": max_rotation_delta["loop_roll"] > 5.0,
            "edge_guide_translation": max_location_delta["edge_guide"] > 5.0,
            "telescope_translation": max_location_delta["telescope_tip"] > 5.0,
            "pre_punch_translation": max_location_delta["pre_punch"] > 1.0,
            "scrap_flap_rotation": max_rotation_delta["scrap_flap"] > 2.0,
            "shear_translation": max_location_delta["shear"] > 1.0,
            "discharge_rotation": max_rotation_delta["discharge_roll"] > 5.0,
        }
        if (status.strip_travel_metres <= initial_status["strip_travel_metres"]
                or status.blanks_produced <= initial_status["blanks_produced"]
                or "RUNNING" not in text.upper() or "BLANKS" not in text.upper()
                or not all(motion_checks.values())):
            finish("RUNTIME_PR008_V074_FAIL__NOT_PROMOTED", f"running/motion checks={motion_checks}")
            return
        station.request_controlled_stop()
        phase = "wait_ready"
        phase_started = now
        return

    if phase == "wait_ready":
        if "READY" not in str(status.state).upper():
            return
        if not station.execute_remote_command(unreal.LBPR008Command.START, SOURCE, AUTHORITY):
            finish("RUNTIME_PR008_V074_FAIL__NOT_PROMOTED", "authorised restart refused")
            return
        phase = "wait_restart_running"
        phase_started = now
        return

    if phase == "wait_restart_running":
        if "RUNNING" not in str(status.state).upper():
            return
        station.set_emergency_stop_active(True)
        after_estop = station.get_hmi_status()
        if "FAULT" not in str(after_estop.state).upper():
            finish("RUNTIME_PR008_V074_FAIL__NOT_PROMOTED",
                   f"E-stop did not enter fault state state={after_estop.state} fault={after_estop.active_fault} "
                   f"power={after_estop.control_power_on} safety={after_estop.safety_circuit_healthy}")
            return
        phase = "wait_estop_fault"
        phase_started = now
        return

    if phase == "wait_estop_fault":
        if "FAULT" not in str(status.state).upper():
            return
        text = hmi_state_text(world)
        fault_status = {"state": str(status.state), "active_fault": str(status.active_fault),
                        "hmi_text": text, "alarm_acknowledged": status.alarm_acknowledged}
        station.set_emergency_stop_active(False)
        if station.reset_fault():
            finish("RUNTIME_PR008_V074_FAIL__NOT_PROMOTED", "E-stop reset without safety reset/ack")
            return
        station.set_safety_circuit_healthy(True)
        if not station.execute_remote_command(unreal.LBPR008Command.ACKNOWLEDGE_ALARM, SOURCE, AUTHORITY):
            finish("RUNTIME_PR008_V074_FAIL__NOT_PROMOTED", "remote alarm acknowledgement refused")
            return
        if not station.execute_remote_command(unreal.LBPR008Command.RESET, SOURCE, AUTHORITY):
            finish("RUNTIME_PR008_V074_FAIL__NOT_PROMOTED", "corrected acknowledged E-stop did not reset")
            return
        if not station.execute_remote_command(unreal.LBPR008Command.REQUEST_ISOLATION, SOURCE, AUTHORITY):
            finish("RUNTIME_PR008_V074_FAIL__NOT_PROMOTED", "remote isolation request refused")
            return
        phase = "wait_isolated"
        phase_started = now
        return

    if phase == "wait_isolated":
        if "ISOLATED" not in str(status.state).upper():
            return
        if not station.confirm_zero_energy_isolation(True, True, unreal.Name("PR008-ZEP-PIE-001")):
            finish("RUNTIME_PR008_V074_FAIL__NOT_PROMOTED", "zero-energy proof refused")
            return
        if not station.execute_remote_command(unreal.LBPR008Command.RELEASE_ISOLATION, SOURCE, AUTHORITY):
            finish("RUNTIME_PR008_V074_FAIL__NOT_PROMOTED", "proved isolation release refused")
            return
        stable = station.capture_save_state()
        isolation_status = {
            "state_after_release": str(station.get_hmi_status().state),
            "save_version": stable.version,
            "evidence_id": "PR008-ZEP-PIE-001",
        }
        if stable.version != 2 or "READY" not in isolation_status["state_after_release"].upper():
            finish("RUNTIME_PR008_V074_FAIL__NOT_PROMOTED", "stable release/save mismatch")
            return
        finish("RUNTIME_PR008_V074_NATIVE_SEQUENCE_MOTION_HMI_SAFETY_ISOLATION_PASS__NOT_PROMOTED")


handle = unreal.register_slate_post_tick_callback(tick)
