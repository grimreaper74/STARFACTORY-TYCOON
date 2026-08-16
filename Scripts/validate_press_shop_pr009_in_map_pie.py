"""Exercise v084 PR-008/PR-009 flow, PR-009 motion, safe restore and isolation in PIE."""

import json
import math
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from press_shop_pr009_in_map_validation_config import TARGET_MAP


unreal.EditorPythonScripting.set_keep_python_script_alive(True)
ROOT = Path(unreal.Paths.project_dir())
MATCH = re.search(r"_v(\d+)$", TARGET_MAP, re.IGNORECASE)
VERSION = f"v{MATCH.group(1)}" if MATCH else "unknown"
PREFIX = f"LB_PR009_V{MATCH.group(1)}_" if MATCH else "LB_PR009_"
OUT = ROOT / "Saved" / "Audits" / f"PR009_InMap_{VERSION}" / "runtime_pie_audit.json"
AUTHORITY = unreal.Name("CW.MW.CONTROL_ROOM")
PR008_SOURCE = unreal.Name("MW.MCR.PR008.CONSOLE")
PR009_SOURCE = unreal.Name("MW.MCR.PR009.CONSOLE")

MOTION = {
    "infeed_rollers": PREFIX + "MOD_PR009_M01_InfeedRoll_01",
    "gantry_bridge": PREFIX + "MOD_PR009_M02_GantryBridge_01",
    "gantry_cross_slide": PREFIX + "MOD_PR009_M03_GantryCrossSlide_01",
    "gantry_z": PREFIX + "MOD_PR009_M04_GantryZ_Carriage_01",
    "lift": PREFIX + "MOD_PR009_M05_LiftTable_01",
    "side_jogger_left": PREFIX + "MOD_PR009_M06_SideJogger_L",
    "end_jogger": PREFIX + "MOD_PR009_M07_EndJogger_01",
    "separator": PREFIX + "MOD_PR009_M08_SeparatorPicker_01",
    "output_rollers": PREFIX + "MOD_PR009_08_OutputRoll_01",
}

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not levels.load_level(TARGET_MAP):
    raise RuntimeError(f"Could not load {TARGET_MAP}")
unreal.EditorLevelLibrary.editor_play_simulate()

started = time.monotonic()
phase_started = started
phase = "wait_world"
handle = None
initial_transforms = {}
stable_restore_transforms = {}
motion_max_location_delta_cm = {key: 0.0 for key in MOTION}
motion_max_rotation_delta_degrees = {key: 0.0 for key in MOTION}
timeline = []
last_state = None
cardinality = {}
binding = {}
blocked_transaction = {}
successful_transfers = []
save_restore = {}
authority_isolation = {}
failures = []
first_cycle_started = False
save_restore_started = False
second_transfer_done = False


def vec(value):
    return [float(value.x), float(value.y), float(value.z)]


def rot(value):
    return [float(value.pitch), float(value.yaw), float(value.roll)]


def angular_delta(a, b):
    return max(abs((x - y + 180.0) % 360.0 - 180.0) for x, y in zip(a, b))


def transform_row(actor):
    return {"location": vec(actor.get_actor_location()), "rotation": rot(actor.get_actor_rotation())}


def delta_rows(current, base):
    return math.dist(current["location"], base["location"]), angular_delta(current["rotation"], base["rotation"])


def finish(status, extra_failure=None):
    global handle
    if extra_failure:
        failures.append(extra_failure)
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    motion_checks = {
        "infeed_rollers": motion_max_rotation_delta_degrees["infeed_rollers"] > 5.0,
        "gantry_bridge": motion_max_location_delta_cm["gantry_bridge"] > 5.0,
        "gantry_cross_slide": motion_max_location_delta_cm["gantry_cross_slide"] > 5.0,
        "gantry_z": motion_max_location_delta_cm["gantry_z"] > 5.0,
        "lift": motion_max_location_delta_cm["lift"] > 5.0,
        "side_jogger": motion_max_location_delta_cm["side_jogger_left"] > 5.0,
        "end_jogger": motion_max_location_delta_cm["end_jogger"] > 5.0,
        "separator": (motion_max_location_delta_cm["separator"] > 5.0
                      or motion_max_rotation_delta_degrees["separator"] > 2.0),
        "output_rollers": motion_max_rotation_delta_degrees["output_rollers"] > 5.0,
    }
    if status.startswith("PASS") and not all(motion_checks.values()):
        failures.append(f"Native-bound presentation motion incomplete: {motion_checks}")
        status = "FAIL__NOT_PROMOTED"
    payload = {
        "$schema": "cairnwell/audit/press-shop-pr009-in-map-pie/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "target_map": TARGET_MAP,
        "target_version": VERSION,
        "status": status if not failures else "FAIL__NOT_PROMOTED",
        "native_cardinality": cardinality,
        "material_flow_binding": binding,
        "state_timeline": timeline,
        "blocked_transaction": blocked_transaction,
        "successful_transfers": successful_transfers,
        "save_restore": save_restore,
        "authority_and_isolation": authority_isolation,
        "motion_actor_labels": MOTION,
        "motion_max_location_delta_cm": motion_max_location_delta_cm,
        "motion_max_rotation_delta_degrees": motion_max_rotation_delta_degrees,
        "motion_checks": motion_checks,
        "failures": failures,
        "promotion_authorized": False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if failures:
        unreal.log_error(f"CAIRNWELL_PR009_IN_MAP_PIE_FAIL failures={failures} output={OUT}")
    else:
        unreal.log(f"CAIRNWELL_PR009_IN_MAP_PIE_PASS output={OUT}")
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()


def tick(_delta_seconds):
    global phase, phase_started, last_state, first_cycle_started, save_restore_started, second_transfer_done
    now = time.monotonic()
    if now - started > 70.0:
        finish("FAIL__NOT_PROMOTED", f"timeout phase={phase}")
        return
    world = unreal.EditorLevelLibrary.get_game_world()
    if world is None:
        return
    pr008s = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBPR008Station)
    pr009s = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBPR009Station)
    flows = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBPressShopMaterialFlowController)
    if phase == "wait_world" and (len(pr008s) != 1 or len(pr009s) != 1 or len(flows) != 1):
        if now - started > 8.0:
            finish("FAIL__NOT_PROMOTED", f"cardinality PR008={len(pr008s)} PR009={len(pr009s)} flow={len(flows)}")
        return
    if len(pr008s) != 1 or len(pr009s) != 1 or len(flows) != 1:
        return
    pr008, pr009, flow = pr008s[0], pr009s[0], flows[0]
    all_actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
    by_label = {actor.get_actor_label(): actor for actor in all_actors}

    if phase == "wait_world":
        cardinality.update({"pr008_count": 1, "pr009_count": 1, "material_flow_count": 1})
        try:
            bound8 = flow.get_editor_property("pr008_station")
            bound9 = flow.get_editor_property("pr009_station")
            binding.update({"property_accessible": True, "pr008_matches": bound8 == pr008, "pr009_matches": bound9 == pr009})
        except Exception as exc:
            binding.update({"property_accessible": False, "error": str(exc), "pr008_matches": False, "pr009_matches": False})
        if not binding["pr008_matches"] or not binding["pr009_matches"]:
            finish("FAIL__NOT_PROMOTED", "PIE material-flow binding mismatch")
            return
        missing = [label for label in MOTION.values() if label not in by_label]
        if missing:
            finish("FAIL__NOT_PROMOTED", f"missing motion actors: {missing}")
            return
        for key, label in MOTION.items():
            initial_transforms[key] = transform_row(by_label[label])

        # Establish deterministic healthy inputs using the native in-map actors.
        # The inherited map may persist PR-008 as Running; an authorised power
        # cycle returns it to Isolated/Ready without fabricating process state.
        if not pr008.execute_remote_command(unreal.LBPR008Command.POWER_OFF, PR008_SOURCE, AUTHORITY):
            finish("FAIL__NOT_PROMOTED", "authorised PR-008 setup power-off refused")
            return
        pr008.set_guards_closed(True)
        pr008.set_strip_available(True)
        pr008.set_strip_loop_percent(50.0)
        pr008.set_edge_tracking_deviation(0.0)
        pr008.set_feed_position_error(0.0)
        pr008.set_feed_servo_healthy(True)
        pr008.set_pre_punch_tool_healthy(True)
        pr008.set_press_shear_load(45.0)
        pr008.set_hydraulic_pressure(215.0)
        pr008.set_slug_chute_fill(12.0)
        pr008.set_scrap_bin_fill(12.0)
        pr008.set_blank_outfeed_clear(True)
        pr008.set_safety_circuit_healthy(True)
        pr008.set_emergency_stop_active(False)
        pr008.set_blank_recipe(1450.0, 60.0)
        pr008.set_measured_cut_length(1450.0)
        if not pr008.execute_remote_command(unreal.LBPR008Command.POWER_ON, PR008_SOURCE, AUTHORITY):
            finish("FAIL__NOT_PROMOTED", "authorised PR-008 power-on refused")
            return
        if not pr008.execute_remote_command(unreal.LBPR008Command.START, PR008_SOURCE, AUTHORITY):
            finish("FAIL__NOT_PROMOTED", "authorised PR-008 start refused")
            return

        pr009.configure_healthy_inputs(False)
        pr009.set_stack_recipe(2, 1, 1.2)
        untrusted = bool(pr009.execute_remote_command(unreal.LBPR009Command.POWER_ON, PR009_SOURCE, unreal.Name("UNTRUSTED")))
        trusted = bool(pr009.execute_remote_command(unreal.LBPR009Command.POWER_ON, PR009_SOURCE, AUTHORITY))
        authority_isolation.update({"untrusted_power_on_rejected": not untrusted, "trusted_power_on_accepted": trusted})
        if untrusted or not trusted:
            finish("FAIL__NOT_PROMOTED", "remote authority power-on contract failed")
            return
        phase = "wait_pr008_blanks"
        phase_started = now
        return

    status = pr009.get_hmi_status()
    state = str(status.state)
    if state != last_state:
        timeline.append({"elapsed_seconds": round(now - started, 3), "state": state,
                         "blank_id": str(status.current_blank_id), "stack_count": status.current_stack_blank_count,
                         "carriers_released": status.carriers_released})
        last_state = state

    for key, label in MOTION.items():
        current = transform_row(by_label[label])
        loc_delta, rotation_delta = delta_rows(current, initial_transforms[key])
        motion_max_location_delta_cm[key] = max(motion_max_location_delta_cm[key], loc_delta)
        motion_max_rotation_delta_degrees[key] = max(motion_max_rotation_delta_degrees[key], rotation_delta)

    if phase == "wait_pr008_blanks":
        if pr008.get_pending_blank_count() < 2:
            return
        pr008.request_controlled_stop()
        pending_before = pr008.get_pending_blank_count()
        oldest_before = str(pr008.get_oldest_pending_blank_id())
        pr009.set_receiver_clear(False)
        blocked_result = bool(flow.transfer_produced_blank_to_pr009(unreal.Name("TX-PR008-PR009-PIE-BLOCKED")))
        blocked_transaction.update({
            "transfer_rejected": not blocked_result,
            "pr008_pending_before": pending_before,
            "pr008_pending_after": pr008.get_pending_blank_count(),
            "pr008_oldest_before": oldest_before,
            "pr008_oldest_after": str(pr008.get_oldest_pending_blank_id()),
            "pr009_blank_after": str(pr009.get_hmi_status().current_blank_id),
            "pr009_upstream_available_after": bool(pr009.get_hmi_status().upstream_blank_available),
        })
        if (blocked_result or blocked_transaction["pr008_pending_after"] != pending_before
                or blocked_transaction["pr008_oldest_after"] != oldest_before
                or blocked_transaction["pr009_blank_after"] not in ("None", "")
                or blocked_transaction["pr009_upstream_available_after"]):
            finish("FAIL__NOT_PROMOTED", "blocked transaction changed ownership or created a phantom blank")
            return
        pr009.set_receiver_clear(True)
        first_id = str(pr008.get_oldest_pending_blank_id())
        before = pr008.get_pending_blank_count()
        if not flow.transfer_produced_blank_to_pr009(unreal.Name("TX-PR008-PR009-PIE-0001")):
            finish("FAIL__NOT_PROMOTED", "first transactional handoff refused")
            return
        after_status = pr009.get_hmi_status()
        successful_transfers.append({
            "transaction_id": "TX-PR008-PR009-PIE-0001", "blank_id": first_id,
            "pr008_pending_before": before, "pr008_pending_after": pr008.get_pending_blank_count(),
            "pr009_owned_blank": str(after_status.current_blank_id),
        })
        if pr008.get_pending_blank_count() != before - 1 or str(after_status.current_blank_id) != first_id:
            finish("FAIL__NOT_PROMOTED", "first handoff identity/ownership mismatch")
            return
        if not pr009.execute_remote_command(unreal.LBPR009Command.START, PR009_SOURCE, AUTHORITY):
            finish("FAIL__NOT_PROMOTED", "authorised PR-009 start refused")
            return
        first_cycle_started = True
        phase = "cycle_and_motion"
        phase_started = now
        return

    if phase == "cycle_and_motion":
        if ("RECEIVING" in state.upper() and status.phase_progress > 0.15
                and not save_restore_started):
            moving_save = pr009.capture_save_state()
            save_restore.update({
                "captured_state": state,
                "captured_blank_id": str(moving_save.current_blank_id),
                "captured_total_blanks": moving_save.total_blanks_stacked,
                "restore_succeeded": bool(pr009.restore_save_state(moving_save)),
            })
            restored = pr009.get_hmi_status()
            save_restore.update({
                "restored_state": str(restored.state),
                "restart_required": bool(restored.restart_required_after_load),
                "restored_blank_id": str(restored.current_blank_id),
            })
            if (not save_restore["restore_succeeded"] or "READY" not in save_restore["restored_state"].upper()
                    or not save_restore["restart_required"]
                    or save_restore["restored_blank_id"] != save_restore["captured_blank_id"]):
                finish("FAIL__NOT_PROMOTED", "moving save did not restore stopped/safe with identity retained")
                return
            save_restore_started = True
            phase = "verify_stopped_restore"
            phase_started = now
            return

    if phase == "verify_stopped_restore":
        # Allow one engine tick for UpdatePresentation to settle every mover at
        # its safe base pose, then measure whether any motion resumes.
        if not stable_restore_transforms:
            stable_restore_transforms.update({key: transform_row(by_label[label]) for key, label in MOTION.items()})
            save_restore["safe_settle_sampled_after_restore"] = True
            phase_started = now
            return
        if now - phase_started < 0.75:
            return
        maximum_stationary_delta = 0.0
        for key, label in MOTION.items():
            loc_delta, rotation_delta = delta_rows(transform_row(by_label[label]), stable_restore_transforms[key])
            maximum_stationary_delta = max(maximum_stationary_delta, loc_delta, rotation_delta)
        save_restore["maximum_stopped_transform_delta"] = maximum_stationary_delta
        if maximum_stationary_delta > 0.1:
            finish("FAIL__NOT_PROMOTED", f"restored station continued unsafe motion delta={maximum_stationary_delta}")
            return
        if not pr009.execute_remote_command(unreal.LBPR009Command.START, PR009_SOURCE, AUTHORITY):
            finish("FAIL__NOT_PROMOTED", "explicit restart after safe restore refused")
            return
        save_restore["explicit_restart_accepted"] = True
        phase = "cycle_and_motion"
        phase_started = now
        return

    if phase == "cycle_and_motion":
        if (status.total_blanks_stacked >= 1 and "RECEIVING" in state.upper()
                and not status.upstream_blank_available and not second_transfer_done):
            if pr008.get_pending_blank_count() < 1:
                finish("FAIL__NOT_PROMOTED", "no second PR-008 blank remained for release-cycle proof")
                return
            second_id = str(pr008.get_oldest_pending_blank_id())
            before = pr008.get_pending_blank_count()
            if not flow.transfer_produced_blank_to_pr009(unreal.Name("TX-PR008-PR009-PIE-0002")):
                finish("FAIL__NOT_PROMOTED", "second transactional handoff refused")
                return
            after = pr009.get_hmi_status()
            successful_transfers.append({
                "transaction_id": "TX-PR008-PR009-PIE-0002", "blank_id": second_id,
                "pr008_pending_before": before, "pr008_pending_after": pr008.get_pending_blank_count(),
                "pr009_owned_blank": str(after.current_blank_id),
            })
            if pr008.get_pending_blank_count() != before - 1 or str(after.current_blank_id) != second_id:
                finish("FAIL__NOT_PROMOTED", "second handoff identity/ownership mismatch")
                return
            second_transfer_done = True
            return
        if status.carriers_released >= 1:
            final_status = pr009.get_hmi_status()
            if str(final_status.current_blank_id) not in ("None", "") or final_status.upstream_blank_available:
                finish("FAIL__NOT_PROMOTED", "phantom blank remains after completed two-blank stack")
                return
            untrusted_request = bool(pr009.execute_remote_command(
                unreal.LBPR009Command.REQUEST_ISOLATION, PR009_SOURCE, unreal.Name("UNTRUSTED")))
            trusted_request = bool(pr009.execute_remote_command(
                unreal.LBPR009Command.REQUEST_ISOLATION, PR009_SOURCE, AUTHORITY))
            invalid_zero = bool(pr009.confirm_zero_energy_isolation(True, False, unreal.Name("PR009-ZEP-PIE-INVALID")))
            release_before_proof = bool(pr009.execute_remote_command(
                unreal.LBPR009Command.RELEASE_ISOLATION, PR009_SOURCE, AUTHORITY))
            valid_zero = bool(pr009.confirm_zero_energy_isolation(True, True, unreal.Name("PR009-ZEP-PIE-001")))
            untrusted_release = bool(pr009.execute_remote_command(
                unreal.LBPR009Command.RELEASE_ISOLATION, PR009_SOURCE, unreal.Name("UNTRUSTED")))
            trusted_release = bool(pr009.execute_remote_command(
                unreal.LBPR009Command.RELEASE_ISOLATION, PR009_SOURCE, AUTHORITY))
            released = pr009.get_hmi_status()
            authority_isolation.update({
                "untrusted_isolation_request_rejected": not untrusted_request,
                "trusted_isolation_request_accepted": trusted_request,
                "incomplete_zero_energy_proof_rejected": not invalid_zero,
                "release_before_zero_energy_proof_rejected": not release_before_proof,
                "complete_zero_energy_proof_accepted": valid_zero,
                "untrusted_isolation_release_rejected": not untrusted_release,
                "trusted_isolation_release_accepted": trusted_release,
                "evidence_id": str(released.last_safety_evidence_id),
                "state_after_release": str(released.state),
            })
            if not all(value for key, value in authority_isolation.items()
                       if key.endswith("_rejected") or key.endswith("_accepted")):
                finish("FAIL__NOT_PROMOTED", "authority/isolation/zero-energy interlock failed")
                return
            finish("PASS__NOT_PROMOTED")


handle = unreal.register_slate_post_tick_callback(tick)
