"""PIE proof of PR-010 map binding, eight-stack flow, save and temporal collision."""

import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path

import unreal


unreal.EditorPythonScripting.set_keep_python_script_alive(True)
ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR010CollisionNavigationCandidate_v099"
OUT = ROOT / "Saved/Audits/PR010_CollisionNavigation/runtime_collision_pie_audit_v099.json"
AUTHORITY = unreal.Name("CW.MW.CONTROL_ROOM")
SOURCE = unreal.Name("PR010_V099_GATE")
KEY_ROLES = ("moving_infeed_shuttle", "moving_carrier_roller", "moving_stop_pin", "moving_reservation_gate", "moving_quality_spur")
CRITICAL_FIXED = ("enclosure_structure", "enclosure_panel", "upper_fascia", "inspection_glazing", "LB.Safety.OpenMesh.Post", "LB.Safety.OpenMesh.Rail", "service_side")

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not levels.load_level(MAP): raise RuntimeError(MAP)
unreal.EditorLevelLibrary.editor_play_simulate()
started = time.monotonic()
handle = None
phase = "boot"
station = None
motion = {}
initial = {}
max_location = {role: 0.0 for role in KEY_ROLES}
max_rotation = {role: 0.0 for role in KEY_ROLES}
fixed = []
baseline_pairs = set()
new_pairs = set()
frames = 0
offered = 0
quality_offered = False
dispatch_requested = False
save_restored = False
authority_checks = {}
state_samples = set()


def tags(actor): return {str(tag) for tag in actor.tags}
def vec(v): return (float(v.x), float(v.y), float(v.z))
def rot(r): return (float(r.roll), float(r.pitch), float(r.yaw))
def angle_delta(a, b): return math.sqrt(sum(min(abs(x-y) % 360.0, 360.0-(abs(x-y) % 360.0)) ** 2 for x, y in zip(a, b)))


def bounds(actor):
    origin, extent = actor.get_actor_bounds(False, False)
    return ((origin.x-extent.x, origin.y-extent.y, origin.z-extent.z), (origin.x+extent.x, origin.y+extent.y, origin.z+extent.z))


def intersects(a, b):
    return all(a[0][i] <= b[1][i] and a[1][i] >= b[0][i] for i in range(3))


def collision_pairs():
    pairs = set()
    for role in ("moving_infeed_shuttle", "moving_reservation_gate", "moving_quality_spur"):
        moving = motion[role]
        mb = bounds(moving)
        for blocker in fixed:
            if intersects(mb, bounds(blocker)):
                pairs.add((moving.get_actor_label(), blocker.get_actor_label()))
    return pairs


def finish(failures):
    global handle
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle); handle = None
    status = station.get_hmi_status() if station else None
    checks = {
        "shuttle_translation": max_location["moving_infeed_shuttle"] > 440.0,
        "lane_roller_rotation": max_rotation["moving_carrier_roller"] > 150.0,
        "lane_stop_translation": max_location["moving_stop_pin"] > 10.0,
        "reservation_gate_rotation": max_rotation["moving_reservation_gate"] > 80.0,
        "quality_spur_translation": max_location["moving_quality_spur"] > 240.0,
    }
    if not all(checks.values()): failures.append(f"presentation motion checks failed: {checks}")
    if new_pairs: failures.append(f"new temporal mover/fixed overlaps: {len(new_pairs)}")
    if not save_restored: failures.append("moving safe-save restoration was not proved")
    if not all(authority_checks.values()): failures.append(f"remote authority checks failed: {authority_checks}")
    if status and (status.total_stacks_stored < 9 or status.total_stacks_dispatched < 1):
        failures.append(f"flow totals too low stored={status.total_stacks_stored} dispatched={status.total_stacks_dispatched}")
    payload = {
        "$schema": "cairnwell/audit/pr010-runtime-collision-pie-v099/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(), "target_map": MAP,
        "status": "PASS__PR010_V099_EIGHT_STACK_QUALITY_HOLD_DISPATCH_MOTION_SAVE_AUTHORITY_TEMPORAL_COLLISION__NOT_PROMOTED" if not failures else "FAIL__PR010_V099_RUNTIME_COLLISION__NOT_PROMOTED",
        "runtime_frames_sampled": frames, "state_samples": sorted(state_samples),
        "authority_checks": authority_checks, "motion_checks": checks,
        "max_location_delta_cm": max_location, "max_rotation_delta_degrees": max_rotation,
        "baseline_overlap_pairs": [list(pair) for pair in sorted(baseline_pairs)],
        "new_temporal_overlap_pairs": [list(pair) for pair in sorted(new_pairs)],
        "safe_save_restore_proved": save_restored,
        "final_hmi": {"state": str(status.state), "stored": status.total_stacks_stored, "dispatched": status.total_stacks_dispatched, "restart_required": status.restart_required_after_load} if status else None,
        "failures": failures, "promotion_authorized": False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if failures: unreal.log_error(f"CAIRNWELL_PR010_RUNTIME_COLLISION_FAIL {failures}")
    else: unreal.log(f"CAIRNWELL_PR010_RUNTIME_COLLISION_PASS {OUT}")
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()


def tick(_delta):
    global phase, station, motion, initial, fixed, baseline_pairs, frames, offered, quality_offered, dispatch_requested, save_restored
    now = time.monotonic()
    if now - started > 55.0:
        finish(["runtime timeout"]); return
    if now - started < 3.0: return
    world = unreal.EditorLevelLibrary.get_game_world()
    if world is None: return
    if station is None:
        stations = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBPR010Station)
        if len(stations) != 1: return
        station = stations[0]
        actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
        for role in KEY_ROLES:
            matches = [actor for actor in actors if role in tags(actor)]
            if not matches: finish([f"missing motion role {role}"]); return
            # Lane A is the representative for repeated lane-role motion.
            motion[role] = next((actor for actor in matches if "LaneA" in actor.get_actor_label()), matches[0])
        fixed = [actor for actor in actors if any(role in tags(actor) for role in CRITICAL_FIXED)]
        for role, actor in motion.items():
            initial[role] = {"location": vec(actor.get_actor_location()), "rotation": rot(actor.get_actor_rotation())}
        baseline_pairs = collision_pairs()
        station.configure_healthy_inputs()
        authority_checks["untrusted_power_rejected"] = not station.execute_remote_command(unreal.LBPR010Command.POWER_ON, SOURCE, unreal.Name("UNTRUSTED"))
        authority_checks["trusted_power_accepted"] = bool(station.execute_remote_command(unreal.LBPR010Command.POWER_ON, SOURCE, AUTHORITY))
        authority_checks["trusted_start_accepted"] = bool(station.execute_remote_command(unreal.LBPR010Command.START, SOURCE, AUTHORITY))
        phase = "fill"

    frames += 1
    status = station.get_hmi_status()
    state_samples.add(str(status.state))
    for role, actor in motion.items():
        max_location[role] = max(max_location[role], math.dist(vec(actor.get_actor_location()), initial[role]["location"]))
        max_rotation[role] = max(max_rotation[role], angle_delta(rot(actor.get_actor_rotation()), initial[role]["rotation"]))
    new_pairs.update(collision_pairs() - baseline_pairs)

    state = str(status.state).upper()
    if phase == "fill" and "RESERVATION_WAIT" in state and str(status.inbound_stack_id).upper() in ("", "NONE"):
        if offered < 8:
            offered += 1
            if not station.offer_upstream_stack(unreal.Name(f"PR009-STACK-V099-{offered:02d}"), False):
                finish([f"stack offer {offered} refused"]); return
        elif status.total_stacks_stored >= 8 and not quality_offered:
            quality_offered = True
            if not station.offer_upstream_stack(unreal.Name("PR009-STACK-V099-QH"), True):
                finish(["quality hold offer refused"]); return
        elif status.total_stacks_stored >= 9 and not dispatch_requested:
            dispatch_requested = True
            if not station.request_lane_dispatch(0, unreal.Name("TRAIN-A-V099")):
                finish(["lane A dispatch refused"]); return
            phase = "dispatch"
    elif phase == "dispatch" and status.total_stacks_dispatched >= 1 and "RESERVATION_WAIT" in state:
        if not station.offer_upstream_stack(unreal.Name("PR009-STACK-V099-SAVE"), False):
            finish(["save-restore stack offer refused"]); return
        phase = "save_wait"
    elif phase == "save_wait" and ("LANE_SELECT" in state or "TRANSFER" in state):
        saved = station.capture_save_state()
        if not station.restore_save_state(saved):
            finish(["moving save restore refused"]); return
        restored = station.get_hmi_status()
        save_restored = "READY" in str(restored.state).upper() and restored.restart_required_after_load and str(restored.inbound_stack_id) == "PR009-STACK-V099-SAVE"
        finish([])


handle = unreal.register_slate_post_tick_callback(tick)
