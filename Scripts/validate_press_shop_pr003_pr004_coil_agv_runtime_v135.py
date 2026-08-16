"""Exact-map PIE gate for the isolated PR003-to-PR004 coil AGV candidates."""

from datetime import datetime, timezone
from pathlib import Path
import json
import os
import time
import unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)

CANDIDATE = os.environ.get("LB_PR003_PR004_AGV_CANDIDATE", "v135").lower()
MAPS = {
    "v135": "/Game/LineBoss/Maps/LB_PressShop_PR003PR004CoilAGVRuntimeCandidate_v135",
    "v136": "/Game/LineBoss/Maps/LB_PressShop_PR003PR004PoweredCHookCandidate_v136",
    "v141": "/Game/LineBoss/Maps/LB_PressShop_PR003PR004PoweredCHookCandidate_v141",
    "v142": "/Game/LineBoss/Maps/LB_PressShop_PR003PR004PoweredCHookVisualProofCandidate_v142",
    "v180": "/Game/LineBoss/Maps/LB_PressShop_PR003PR004CoilReadabilityCandidate_v180",
    "v190": "/Game/LineBoss/Maps/LB_PressShop_PR003PR004HookLightingMergeCandidate_v190",
    "v140": "/Game/LineBoss/Maps/LB_PressShop_PR003PR004CoilReadabilityCandidate_v140",
}
if CANDIDATE not in MAPS:
    raise RuntimeError(f"Unknown LB_PR003_PR004_AGV_CANDIDATE={CANDIDATE!r}")
MAP = MAPS[CANDIDATE]
OUT = Path(unreal.Paths.project_saved_dir()) / f"Audits/press_shop_pr003_pr004_coil_agv_runtime_{CANDIDATE}.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

OUT.parent.mkdir(parents=True, exist_ok=True)
if OUT.exists():
    OUT.unlink()
unreal.EditorLevelLibrary.editor_play_simulate()
started = time.monotonic()
handle = None
controller = None
chassis = None
deck = None
load = None
saved_state = None
saved_location = None
fault_location = None
stage = "bind"
stage_started = started
phase_trace = []
checks = {}
failures = []


def tagged(world, tag):
    return list(unreal.GameplayStatics.get_all_actors_with_tag(world, unreal.Name(tag)))


def same(a, b, tolerance=0.1):
    return (a - b).length() <= tolerance


def record(name, passed, detail):
    checks[name] = {"passed": bool(passed), "detail": detail}
    if not passed:
        failures.append(f"{name}: {detail}")


def finish():
    global handle
    payload = {
        "$schema": f"cairnwell/audit/press-shop-pr003-pr004-coil-agv-runtime-{CANDIDATE}/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS__EXACT_MAP_PIE_RUNTIME_GATE__NOT_PROMOTED" if not failures else "FAIL__EXACT_MAP_PIE_RUNTIME_GATE__NOT_PROMOTED",
        "map": MAP,
        "inventory_model": "ELEVEN_STORED_PLUS_ONE_PHYSICAL_IN_TRANSFER",
        "candidate_coil_id": "MCX-U-CS06-CANDIDATE",
        "phase_trace": phase_trace,
        "checks": checks,
        "failures": failures,
        "performance_authority": "GAMEPLAY_TUNING_ONLY__REAL_PERFORMANCE_AND_CERTIFICATION_TBC",
        "promotion_authorized": False
    }
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    unreal.log(json.dumps(payload, indent=2))
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.SystemLibrary.quit_editor()


def tick(_delta_seconds):
    global controller, chassis, deck, load, saved_state, saved_location
    global fault_location, stage, stage_started
    now = time.monotonic()
    if now - started > 75.0:
        record("runtime_timeout", False, f"stage={stage}")
        finish()
        return
    world = unreal.EditorLevelLibrary.get_game_world()
    if world is None:
        return

    if controller is None:
        controllers = list(unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBCoilAGVController))
        chassis_list = [a for a in tagged(world,"LB.Vehicle.CoilAGV") if not a.actor_has_tag(unreal.Name("LB.Vehicle.CoilAGV.LiftDeck"))]
        decks = tagged(world,"LB.Vehicle.CoilAGV.LiftDeck")
        loads = tagged(world,"LB.Inventory.InTransfer")
        stored = []
        for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.StaticMeshActor):
            tags = {str(tag) for tag in actor.tags}
            if "LB.Material.PackagedCoil" in tags and any(tag.startswith("LB.PR003.Layout.Slot.") for tag in tags) and "LB.Inventory.InTransfer" not in tags:
                stored.append(actor)
        record("one_runtime_controller", len(controllers)==1, f"count={len(controllers)}")
        record("one_chassis", len(chassis_list)==1, f"count={len(chassis_list)}")
        record("one_lift_deck", len(decks)==1, f"count={len(decks)}")
        record("one_physical_transfer_coil", len(loads)==1, f"count={len(loads)}")
        record("eleven_stored_coils", len(stored)==11, f"count={len(stored)}")
        if failures:
            finish(); return
        controller, chassis, deck, load = controllers[0], chassis_list[0], decks[0], loads[0]
        controller.set_editor_property("custom_time_dilation", 4.0)
        record("exact_binding", controller.discover_and_bind(), "DiscoverAndBind")
        record("control_power", controller.set_control_power(True), "enabled")
        record("safe_inputs", controller.set_safety_inputs(True,True,True,True,True,True,True), "all proved")
        record("dispatch_started", controller.start_dispatch("MCX-U-CS06-CANDIDATE"), str(controller.get_phase()))
        if failures:
            finish(); return
        stage = "await_turn"
        stage_started = now
        return

    phase = str(controller.get_phase())
    if not phase_trace or phase_trace[-1] != phase:
        phase_trace.append(phase)

    if stage == "await_turn" and controller.get_phase() == unreal.LBCoilAGVPhase.TRAVEL_TO_DOCK:
        fault_location = controller.get_vehicle_location()
        controller.set_safety_inputs(True,True,False,True,True,True,True)
        record("scanner_fault_latched", controller.get_fault()==unreal.LBCoilAGVFault.SCANNER_OBSTRUCTED, str(controller.get_fault()))
        stage = "prove_scanner_stop"
        stage_started = now
        return

    if stage == "prove_scanner_stop" and now-stage_started > 0.5:
        record("scanner_fail_stop_no_drift", same(controller.get_vehicle_location(),fault_location,0.1), str(controller.get_vehicle_location()))
        record("unsafe_reset_rejected", not controller.reset_fault(unreal.Name("EVID_SCANNER_STILL_BLOCKED")), "reset result")
        controller.set_safety_inputs(True,True,True,True,True,True,True)
        record("named_scanner_recovery", controller.reset_fault(unreal.Name(f"EVID_SCANNER_CLEAR_{CANDIDATE.upper()}")), str(controller.get_phase()))
        saved_state = controller.get_save_state()
        saved_location = controller.get_vehicle_location()
        record("in_flight_save_created", saved_state is not None, str(saved_state))
        stage = "move_after_save"
        stage_started = now
        return

    if stage == "move_after_save" and now-stage_started > 0.5:
        moved = not same(controller.get_vehicle_location(), saved_location, 1.0)
        record("travel_progress_after_save", moved, str(controller.get_vehicle_location()))
        record("stable_phase_restore", saved_state is not None and controller.restore_save_state(saved_state), "restore result")
        record("restore_location_exact", same(controller.get_vehicle_location(),saved_location,0.1), str(controller.get_vehicle_location()))
        controller.set_safety_inputs(True,True,True,True,True,False,True)
        record("crane_envelope_fault_latched", controller.get_fault()==unreal.LBCoilAGVFault.CRANE_ENVELOPE_CONFLICT, str(controller.get_fault()))
        stage = "prove_crane_stop"
        stage_started = now
        fault_location = controller.get_vehicle_location()
        return

    if stage == "prove_crane_stop" and now-stage_started > 0.5:
        record("crane_conflict_no_drift", same(controller.get_vehicle_location(),fault_location,0.1), str(controller.get_vehicle_location()))
        controller.set_safety_inputs(True,True,True,True,True,True,True)
        record("named_crane_recovery", controller.reset_fault(unreal.Name(f"EVID_CRANE_ENVELOPE_CLEAR_{CANDIDATE.upper()}")), str(controller.get_phase()))
        stage = "await_handoff"
        stage_started = now
        return

    if stage == "await_handoff" and controller.is_handoff_ready():
        expected = unreal.Vector(-5550.0,-2000.0,chassis.get_actor_location().z)
        record("handoff_ready", True, str(controller.get_phase()))
        record("dock_location", same(controller.get_vehicle_location(),expected,0.2), str(controller.get_vehicle_location()))
        record("dock_yaw_90", abs(controller.get_vehicle_yaw_degrees()-90.0)<=0.1, str(controller.get_vehicle_yaw_degrees()))
        record("deck_lift_80mm", abs(controller.get_lift_height_cm()-8.0)<=0.02, str(controller.get_lift_height_cm()))
        record("load_rigid_registration", controller.get_max_load_follow_error_cm()<=0.1, str(controller.get_max_load_follow_error_cm()))
        record("load_still_owned", load.actor_has_tag(unreal.Name("LB.Inventory.InTransfer")), str(load.tags))
        record("runtime_authority_not_promoted", controller.actor_has_tag(unreal.Name("LB.Asset.CandidateNotPromoted")), str(controller.tags))
        finish()


handle = unreal.register_slate_post_tick_callback(tick)
