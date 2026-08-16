"""Exact-map PIE gate for the v222 playable Press Shop management concept."""

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import unreal


unreal.EditorPythonScripting.set_keep_python_script_alive(True)
ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v222"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_playable_management_pie_v222.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
unreal.EditorLevelLibrary.editor_play_simulate()

started = time.monotonic()
phase = "wait_world"
phase_started = started
handle = None
evidence = {}


def enum_text(value):
    return str(value).split(".")[-1]


def finish(failures):
    global handle
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    payload = {
        "$schema": "cairnwell/audit/press-shop-playable-management-pie-v222/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS__EXACT_MAP_RUNTIME_AUTHORITIES_CONSOLE_START_PAUSE_STOP_AND_TRAIN_ISOLATION__VISUAL_GATE_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__EXACT_MAP_PLAYABLE_MANAGEMENT_PIE__NOT_PROMOTED",
        "map": MAP,
        "test_material_policy": "ephemeral PIE-only coil and reserved blank; no package/save mutation",
        "evidence": evidence,
        "failures": failures,
        "promotion_authorized": False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    unreal.log(f"LB_V222_MANAGEMENT_PIE_{'PASS' if not failures else 'FAIL'}::{json.dumps(payload)}")
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()


def tick(_delta):
    global phase, phase_started
    try:
        now = time.monotonic()
        if now - started > 50.0:
            finish([f"timeout in phase {phase}"])
            return
        world = unreal.EditorLevelLibrary.get_game_world()
        if world is None:
            return
        if phase == "wait_world" and now - phase_started >= 4.0:
            failures = []
            actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
            by_class = {}
            for actor in actors:
                name = actor.get_class().get_name()
                by_class.setdefault(name, []).append(actor)
            required = {
                "LBPR004Station": 1, "LBPR005Station": 1, "LBPR006Station": 1,
                "LBPR007Station": 1, "LBPR008Station": 1, "LBPR009Station": 1,
                "LBPR010Station": 1, "LBPressShopMaterialFlowController": 1,
                "LBPressTrainAStation": 4, "LBControlRoomOperationsConsole": 1,
            }
            for name, count in required.items():
                if len(by_class.get(name, [])) != count:
                    failures.append(f"{name}: expected {count}, found {len(by_class.get(name, []))}")
            starts = [actor for actor in actors if isinstance(actor, unreal.PlayerStart)]
            if len(starts) != 1:
                failures.append(f"PlayerStart: expected 1, found {len(starts)}")
            evidence["runtime_authority_counts"] = {name: len(by_class.get(name, [])) for name in required}
            evidence["player_start_count"] = len(starts)
            if failures:
                finish(failures)
                return

            console = by_class["LBControlRoomOperationsConsole"][0]
            pr005 = by_class["LBPR005Station"][0]
            trains = sorted(by_class["LBPressTrainAStation"], key=lambda actor: str(actor.get_hmi_status().train_id))
            train_ids = [str(actor.get_hmi_status().train_id) for actor in trains]
            evidence["train_ids"] = train_ids
            if train_ids != ["TRAIN_A", "TRAIN_B", "TRAIN_C", "TRAIN_D"]:
                finish([f"unexpected train IDs {train_ids}"])
                return
            assigned = console.get_assigned_press_train()
            if assigned is None or str(assigned.get_hmi_status().train_id) != "TRAIN_A":
                finish(["console did not bind default selected TRAIN_A"])
                return

            # Prove the user-facing hold before introducing ephemeral test material.
            console.increase_quantity()
            console.toggle_operating_mode()
            console.create_production_order()
            start_without_authority = console.start_or_resume_order()
            held_state = console.capture_save_state()
            evidence["honest_start_hold"] = {
                "accepted": bool(start_without_authority),
                "alarm": held_state.last_alarm,
            }
            if start_without_authority:
                finish(["console started without recipe/material authority"])
                return

            # Configure normal commissioning permissives using public station APIs.
            pr005.set_control_power(True)
            pr005.set_utilities_available(True)
            pr005.load_coil("AUTOMATION_ONLY_V222_COIL", 1500.0)
            pr005.set_coil_car_positioned(True)
            pr005.set_mandrel_expanded(True)
            pr005.set_keeper_and_snubber(True, True)
            pr005.set_guards_closed(True)
            pr005.set_safety_circuit_healthy(True)
            pr005.set_strip_threaded(True)
            if not console.resolve_recipe_authority(unreal.Name("ROOF_OUTER"), 1500.0):
                finish(["console rejected test recipe authority"])
                return
            console.create_production_order()

            train_a = trains[0]
            train_a.set_access_interlocks_closed(True)
            train_a.set_safety_circuit_healthy(True)
            train_a.set_emergency_stop_active(False)
            train_a.set_destack_healthy(True)
            train_a.set_transfer_healthy(True)
            train_a.set_hydraulic_pressure(280.0)
            train_a.set_press_load(45.0)
            train_a.set_inspection_healthy(True)
            train_a.set_stillage_output_clear(True)
            train_a.set_target_strokes_per_minute(10.0)
            if not train_a.queue_reserved_blank(
                    unreal.Name("AUTOMATION_ONLY_V222_RESERVATION"),
                    unreal.Name("AUTOMATION_ONLY_V222_BLANK")):
                finish(["TRAIN_A rejected ephemeral reserved blank"])
                return
            before = {str(actor.get_hmi_status().train_id): enum_text(actor.get_hmi_status().state) for actor in trains}
            accepted = console.start_or_resume_order()
            after = {str(actor.get_hmi_status().train_id): enum_text(actor.get_hmi_status().state) for actor in trains}
            evidence["start_route"] = {"accepted": bool(accepted), "before": before, "after": after}
            if not accepted or "CYCL" not in after["TRAIN_A"].upper():
                finish([f"selected TRAIN_A did not enter cycle: {evidence['start_route']}"])
                return
            if any(after[name] != before[name] for name in ("TRAIN_B", "TRAIN_C", "TRAIN_D")):
                finish([f"non-selected train state changed: {evidence['start_route']}"])
                return
            phase = "pause"
            phase_started = now
            return

        if phase == "pause" and now - phase_started >= 0.5:
            console = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBControlRoomOperationsConsole)[0]
            trains = sorted(
                unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBPressTrainAStation),
                key=lambda actor: str(actor.get_hmi_status().train_id))
            paused = console.pause_order()
            states = {str(actor.get_hmi_status().train_id): enum_text(actor.get_hmi_status().state) for actor in trains}
            evidence["pause_route"] = {"accepted": bool(paused), "states": states}
            if not paused or not any(token in states["TRAIN_A"].upper() for token in ("STOP", "READY")):
                finish([f"selected TRAIN_A controlled pause failed: {evidence['pause_route']}"])
                return
            stopped = console.stop_order()
            console.cycle_assigned_train()
            selected = console.get_assigned_press_train()
            evidence["stop_and_selection"] = {
                "stop_accepted": bool(stopped),
                "selected_train": str(selected.get_hmi_status().train_id) if selected else None,
            }
            if not stopped or selected is None or str(selected.get_hmi_status().train_id) != "TRAIN_B":
                finish([f"stop or Train B selection failed: {evidence['stop_and_selection']}"])
                return
            finish([])
    except Exception as exc:
        finish([f"validator exception: {type(exc).__name__}: {exc}"])


handle = unreal.register_slate_post_tick_callback(tick)

