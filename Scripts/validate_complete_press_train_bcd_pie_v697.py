"""Sequential PIE identity, authority, process and P0 motion proof for complete Trains B-D."""
from datetime import datetime, timezone
from pathlib import Path
import json
import time
import unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
ROOT = Path(unreal.Paths.project_dir())
OUT = ROOT / "Saved/Audits/PressTrains/complete_press_train_bcd_pie_v697.json"
AUTH = unreal.Name("CW.MW.CONTROL_ROOM")
SPECS = [
    ("B", "FLOORS / UNDERBODY"),
    ("C", "CLOSURES"),
    ("D", "REINFORCEMENTS / SMALL PANELS"),
]
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if OUT.exists():
    raise RuntimeError("Refusing to overwrite v697")

handle = None
index = -1
phase = "advance"
phase_started = time.monotonic()
roles = {}
rest = {}
metrics = {}
checks = {}
failures = []
reports = {}

def tags(actor): return {str(tag) for tag in actor.tags}
def distance(a, b): return (a - b).length()
def angle_delta(a, b): return abs((a - b + 180.0) % 360.0 - 180.0)

def finish_all():
    global handle
    if handle:
        unreal.unregister_slate_post_tick_callback(handle); handle = None
    payload = {
        "revision": "v697", "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS__TRAINS_B_D_IDENTITY_AUTHORITY_PROCESS_AND_P0_MOTION" if not failures else "FAIL__TRAINS_B_D_PIE",
        "variants": reports, "failures": failures, "meshy_credits_used": 0,
        "protected_map_modified": False, "promotion_authorized": False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (unreal.log if not failures else unreal.log_error)(
        "LINE_BOSS_COMPLETE_PRESS_TRAIN_BCD_PIE_V697_" + ("PASS" if not failures else "FAIL"))
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()

def complete_variant():
    global phase, phase_started
    letter, family = SPECS[index]
    checks.update({
        "destack_lift_moves": metrics["destack"] > 5.0,
        "four_transfer_crossbars_move": metrics["transfer"] > 10.0,
        "articulated_unload_robot_moves": metrics["unload"] > 5.0,
    })
    local_failures = [key for key, passed in checks.items() if not passed]
    failures.extend(f"Train {letter}: {item}" for item in local_failures)
    reports[letter] = {
        "map": f"/Game/LineBoss/Developer/Validation/PressTrains/LB_PressTrain{letter}_CompleteVariant_v696",
        "train_id": f"TRAIN_{letter}", "part_family": family,
        "role_counts": {k: len(v) for k, v in roles.items()},
        "max_destack_translation_delta_cm": metrics["destack"],
        "min_of_four_transfer_translation_delta_cm": metrics["transfer"],
        "max_unload_shoulder_yaw_delta_deg": metrics["unload"],
        "checks": dict(checks), "failures": local_failures,
    }
    unreal.EditorLevelLibrary.editor_end_play()
    phase = "advance"
    phase_started = time.monotonic()

def tick(_):
    global index, phase, phase_started, roles, rest, metrics, checks
    now = time.monotonic()
    if now - phase_started > 55.0:
        failures.append(f"timeout at variant index {index}, phase {phase}"); finish_all(); return
    if phase == "advance":
        if unreal.EditorLevelLibrary.get_game_world(): return
        index += 1
        if index >= len(SPECS): finish_all(); return
        letter, _ = SPECS[index]
        target = f"/Game/LineBoss/Developer/Validation/PressTrains/LB_PressTrain{letter}_CompleteVariant_v696"
        if not levels.load_level(target):
            failures.append(f"Train {letter}: map load failed"); finish_all(); return
        roles, rest, checks = {}, {}, {}
        metrics = {"destack": 0.0, "transfer": 0.0, "unload": 0.0}
        unreal.EditorLevelLibrary.editor_play_simulate()
        phase = "discover"; phase_started = now; return
    world = unreal.EditorLevelLibrary.get_game_world()
    if not world: return
    trains = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBPressTrainAStation)
    if phase == "discover":
        if len(trains) != 1 or now - phase_started < 3.0: return
        letter, family = SPECS[index]
        static_actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.StaticMeshActor)
        roles = {
            "destack_lift": [a for a in static_actors if "LB.PressTrain.Role.destack_lift" in tags(a)],
            "transfer_crossbar": [a for a in static_actors if "LB.PressTrain.Role.transfer_crossbar" in tags(a)],
            "unload_robot_shoulder_runtime": [a for a in static_actors if "LB.PressTrain.Role.unload_robot_shoulder_runtime" in tags(a)],
        }
        train = trains[0]
        status = train.get_hmi_status()
        expected_roles = {"destack_lift": 3, "transfer_crossbar": 4, "unload_robot_shoulder_runtime": 1}
        checks = {
            "one_native_authority": len(trains) == 1,
            "train_identity_matches": str(status.train_id) == f"TRAIN_{letter}",
            "part_family_matches": train.get_part_family() == family,
            "separated_role_counts_match": all(len(roles[k]) == v for k, v in expected_roles.items()),
        }
        if not all(checks.values()): complete_variant(); return
        rest = {
            "destack": {a.get_actor_label(): a.get_actor_location() for a in roles["destack_lift"]},
            "transfer": {a.get_actor_label(): a.get_actor_location() for a in roles["transfer_crossbar"]},
            "unload": roles["unload_robot_shoulder_runtime"][0].get_actor_rotation().yaw,
        }
        train.set_access_interlocks_closed(True); train.set_safety_circuit_healthy(True)
        train.set_emergency_stop_active(False); train.set_destack_healthy(True)
        train.set_transfer_healthy(True); train.set_hydraulic_pressure(280); train.set_press_load(45)
        train.set_inspection_healthy(True); train.set_stillage_output_clear(True)
        train.set_target_strokes_per_minute(10)
        checks["reserved_blank_accepted"] = bool(train.queue_reserved_blank(
            unreal.Name(f"RES-V697-{letter}"), unreal.Name(f"PR010-BLANK-V697-{letter}")))
        source = unreal.Name(f"MW.MCR.TRAIN_{letter}.CONSOLE")
        checks["trusted_power_accepted"] = bool(train.execute_remote_command(
            unreal.LBPressTrainACommand.POWER_ON, source, AUTH))
        checks["trusted_start_accepted"] = bool(train.execute_remote_command(
            unreal.LBPressTrainACommand.START, source, AUTH))
        if not all(checks.values()): complete_variant(); return
        phase = "cycling"; phase_started = now; return
    if phase == "cycling":
        train = trains[0]
        for actor in roles["destack_lift"]:
            metrics["destack"] = max(metrics["destack"], distance(actor.get_actor_location(), rest["destack"][actor.get_actor_label()]))
        deltas = [distance(a.get_actor_location(), rest["transfer"][a.get_actor_label()]) for a in roles["transfer_crossbar"]]
        if deltas: metrics["transfer"] = max(metrics["transfer"], min(deltas))
        shoulder = roles["unload_robot_shoulder_runtime"][0]
        metrics["unload"] = max(metrics["unload"], angle_delta(shoulder.get_actor_rotation().yaw, rest["unload"]))
        if train.get_hmi_status().cycle_progress > .985: complete_variant()

handle = unreal.register_slate_post_tick_callback(tick)
