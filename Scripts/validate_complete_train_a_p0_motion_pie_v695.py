"""PIE proof that separated P0 destack, transfer and unload presentations move."""
from pathlib import Path
from datetime import datetime, timezone
import json
import time
import unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
ROOT = Path(unreal.Paths.project_dir())
TARGET = "/Game/LineBoss/Developer/Validation/PressTrains/LB_PressTrainA_RuntimeP0_v694"
OUT = ROOT / r"Saved\Audits\PressTrains\complete_train_a_p0_motion_pie_v695.json"
AUTH = unreal.Name("CW.MW.CONTROL_ROOM")
SOURCE = unreal.Name("MW.MCR.TRAIN_A.CONSOLE")
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if OUT.exists():
    raise RuntimeError("Refusing to overwrite v695")
if not levels.load_level(TARGET):
    raise RuntimeError("Could not load v694")
unreal.EditorLevelLibrary.editor_play_simulate()

started = time.monotonic()
handle = None
state = "discover"
rest = {}
roles = {}
max_destack_delta = 0.0
max_transfer_delta = 0.0
max_unload_yaw_delta = 0.0
checks = {}
failures = []

def tags(actor):
    return {str(tag) for tag in actor.tags}

def angle_delta(a, b):
    return abs((a - b + 180.0) % 360.0 - 180.0)

def distance(a, b):
    return (a - b).length()

def finish():
    global handle
    if handle:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    checks.update({
        "destack_lift_moves": max_destack_delta > 5.0,
        "four_transfer_crossbars_move": max_transfer_delta > 10.0,
        "articulated_unload_robot_moves": max_unload_yaw_delta > 5.0,
    })
    for key in ("destack_lift_moves", "four_transfer_crossbars_move", "articulated_unload_robot_moves"):
        if not checks[key]:
            failures.append(key + " failed")
    payload = {
        "revision": "v695",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "target_map": TARGET,
        "status": "PASS__SEPARATED_P0_RUNTIME_MOTION__NOT_PROMOTED" if not failures else "FAIL__NOT_PROMOTED",
        "role_counts": {key: len(value) for key, value in roles.items()},
        "max_destack_translation_delta_cm": max_destack_delta,
        "max_transfer_translation_delta_cm": max_transfer_delta,
        "max_unload_shoulder_yaw_delta_deg": max_unload_yaw_delta,
        "checks": checks,
        "failures": failures,
        "meshy_credits_used": 0,
        "protected_map_modified": False,
        "promotion_authorized": False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (unreal.log if not failures else unreal.log_error)(
        "LINE_BOSS_COMPLETE_TRAIN_A_P0_MOTION_V695_" + ("PASS" if not failures else "FAIL"))
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()

def tick(_):
    global state, roles, rest, max_destack_delta, max_transfer_delta, max_unload_yaw_delta
    now = time.monotonic()
    if now - started > 45.0:
        failures.append("runtime validation timeout at " + state)
        finish()
        return
    world = unreal.EditorLevelLibrary.get_game_world()
    if not world:
        return
    trains = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBPressTrainAStation)
    if state == "discover":
        if len(trains) != 1 or now - started < 3.0:
            return
        static_actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.StaticMeshActor)
        roles = {
            "destack_lift": [a for a in static_actors if "LB.PressTrain.Role.destack_lift" in tags(a)],
            "transfer_crossbar": [a for a in static_actors if "LB.PressTrain.Role.transfer_crossbar" in tags(a)],
            "unload_robot_shoulder_runtime": [a for a in static_actors if "LB.PressTrain.Role.unload_robot_shoulder_runtime" in tags(a)],
        }
        expected = {"destack_lift": 3, "transfer_crossbar": 4, "unload_robot_shoulder_runtime": 1}
        checks["one_native_authority"] = len(trains) == 1
        checks["separated_role_counts_match"] = all(len(roles[key]) == count for key, count in expected.items())
        if not checks["separated_role_counts_match"]:
            failures.append(f"role counts { {key: len(value) for key, value in roles.items()} } expected {expected}")
            finish()
            return
        rest = {
            "destack": {a.get_actor_label(): a.get_actor_location() for a in roles["destack_lift"]},
            "transfer": {a.get_actor_label(): a.get_actor_location() for a in roles["transfer_crossbar"]},
            "unload_yaw": roles["unload_robot_shoulder_runtime"][0].get_actor_rotation().yaw,
        }
        train = trains[0]
        train.set_access_interlocks_closed(True)
        train.set_safety_circuit_healthy(True)
        train.set_emergency_stop_active(False)
        train.set_destack_healthy(True)
        train.set_transfer_healthy(True)
        train.set_hydraulic_pressure(280)
        train.set_press_load(45)
        train.set_inspection_healthy(True)
        train.set_stillage_output_clear(True)
        train.set_target_strokes_per_minute(10)
        checks["reserved_blank_accepted"] = bool(train.queue_reserved_blank(
            unreal.Name("RES-V695-001"), unreal.Name("PR010-BLANK-V695-001")))
        checks["trusted_power_accepted"] = bool(train.execute_remote_command(
            unreal.LBPressTrainACommand.POWER_ON, SOURCE, AUTH))
        checks["trusted_start_accepted"] = bool(train.execute_remote_command(
            unreal.LBPressTrainACommand.START, SOURCE, AUTH))
        if not all(checks[key] for key in ("reserved_blank_accepted", "trusted_power_accepted", "trusted_start_accepted")):
            failures.append("native process start failed")
            finish()
            return
        state = "cycling"
        return
    if state == "cycling":
        train = trains[0]
        for actor in roles["destack_lift"]:
            max_destack_delta = max(max_destack_delta, distance(
                actor.get_actor_location(), rest["destack"][actor.get_actor_label()]))
        transfer_deltas = []
        for actor in roles["transfer_crossbar"]:
            delta = distance(actor.get_actor_location(), rest["transfer"][actor.get_actor_label()])
            transfer_deltas.append(delta)
        if transfer_deltas:
            max_transfer_delta = max(max_transfer_delta, min(transfer_deltas))
        shoulder = roles["unload_robot_shoulder_runtime"][0]
        max_unload_yaw_delta = max(max_unload_yaw_delta, angle_delta(
            shoulder.get_actor_rotation().yaw, rest["unload_yaw"]))
        status = train.get_hmi_status()
        if status.cycle_progress > 0.985:
            finish()

handle = unreal.register_slate_post_tick_callback(tick)
