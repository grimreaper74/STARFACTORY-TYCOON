"""PIE proof for Train A v018 standing-player collision, navigation and robot sweeps."""

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
root = Path(unreal.Paths.project_dir())
map_path = "/Game/LineBoss/Maps/LB_PressTrainAPhysicalGameplayCandidate_v018"
out = root / "Saved/Audits/PressTrains/press_train_a_physical_pie_v018.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not levels.load_level(map_path):
    raise RuntimeError(map_path)
unreal.EditorLevelLibrary.editor_play_simulate()
started = time.monotonic()
phase = "wait_world"
phase_started = started
handle = None
initial_evidence = {}
overlap_pairs = set()
robot_bounds_min = [1e12, 1e12, 1e12]
robot_bounds_max = [-1e12, -1e12, -1e12]
AUTHORITY = unreal.Name("CW.MW.CONTROL_ROOM")
SOURCE = unreal.Name("MW.MCR.TRAIN_A.CONSOLE")


def actor_tags(actor):
    return {str(value) for value in actor.tags}


def hit_row(result, start, end, shape=None):
    if result is None:
        return {"start_cm": start, "end_cm": end, "shape": shape, "hit": False,
                "hit_actor": None, "impact_point_cm": None}
    values = result.to_tuple(); hit = bool(values[0])
    actor = values[9] if hit else None
    return {"start_cm": start, "end_cm": end, "shape": shape, "hit": hit,
            "hit_actor": actor.get_actor_label() if actor else None,
            "impact_point_cm": [values[5].x, values[5].y, values[5].z] if hit else None}


def line(world, start, end, ignored=None):
    result = unreal.SystemLibrary.line_trace_single(
        world, unreal.Vector(*start), unreal.Vector(*end), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
        False, ignored or [], unreal.DrawDebugTrace.NONE, True)
    return hit_row(result, start, end, "line")


def capsule(world, start, end, radius=34.0, half_height=87.0, ignored=None):
    result = unreal.SystemLibrary.capsule_trace_single(
        world, unreal.Vector(*start), unreal.Vector(*end), radius, half_height,
        unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, ignored or [], unreal.DrawDebugTrace.NONE, True)
    return hit_row(result, start, end, {"type": "capsule", "radius_cm": radius,
                                       "half_height_cm": half_height})


def finish(failures, extra=None):
    global handle
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle); handle = None
    payload = {
        "$schema": "cairnwell/audit/press-train-a-physical-pie-v018/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS__V018_STANDING_PLAYER_FLOOR_AISLE_NAVIGATION_GUARDING_QUERY_MOVER_AND_ROBOT_SWEEP_GATE__NOT_PROMOTED"
                  if not failures else "FAIL__V018_PHYSICAL_PIE_GATE__NOT_PROMOTED",
        "map": map_path, "initial_physical_evidence": initial_evidence,
        "robot_motion_swept_bounds_cm": {"min": robot_bounds_min, "max": robot_bounds_max},
        "robot_blocking_overlap_pairs": sorted([list(pair) for pair in overlap_pairs]),
        "failures": failures, "production_map_changed": False, "promotion_authorized": False,
    }
    if extra:
        payload.update(extra)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    unreal.log(f"PRESS_TRAIN_A_V018_PHYSICAL_PIE_{'PASS' if not failures else 'FAIL'} output={out}")
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()


def initial_checks(world):
    actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
    blocking = [actor for actor in actors if "LB.Collision.TrainA.Blocking.v018" in actor_tags(actor)]
    query = [actor for actor in actors if "LB.Collision.TrainA.QueryMover.v018" in actor_tags(actor)]
    starts = [actor for actor in actors if isinstance(actor, unreal.PlayerStart)
              and "LB.PlayerStart.StandingOperator" in actor_tags(actor)]
    foundation = next((actor for actor in blocking
                       if "LB.PressTrain.Role.planning_envelope_foundation" in actor_tags(actor)), None)
    failures = []
    if len(blocking) != 61: failures.append(f"expected 61 runtime blockers, found {len(blocking)}")
    if len(query) != 65: failures.append(f"expected 65 runtime query movers, found {len(query)}")
    if len(starts) != 1: failures.append(f"expected one runtime standing start, found {len(starts)}")
    if foundation is None: failures.append("foundation blocker missing")
    pawn = unreal.GameplayStatics.get_player_pawn(world, 0)
    capsule_component = pawn.get_component_by_class(unreal.CapsuleComponent) if pawn else None
    pawn_row = {"present": pawn is not None,
                "class": pawn.get_class().get_name() if pawn else None,
                "location_cm": ([pawn.get_actor_location().x, pawn.get_actor_location().y,
                                  pawn.get_actor_location().z] if pawn else None),
                "capsule_radius_cm": capsule_component.get_unscaled_capsule_radius() if capsule_component else None,
                "capsule_half_height_cm": capsule_component.get_unscaled_capsule_half_height() if capsule_component else None}
    if not pawn or not capsule_component: failures.append(f"standing operator pawn/capsule missing: {pawn_row}")
    elif abs(pawn_row["capsule_radius_cm"] - 34.0) > 0.1 or abs(pawn_row["capsule_half_height_cm"] - 88.0) > 0.1:
        failures.append(f"standing operator capsule authority mismatch: {pawn_row}")
    ignored_except_foundation = [actor for actor in actors if actor != foundation]
    floor_trace = line(world, (680, 600, 200), (680, 600, -50), ignored_except_foundation)
    if not floor_trace["hit"] or "Foundation" not in (floor_trace["hit_actor"] or ""):
        failures.append(f"standing floor trace failed: {floor_trace}")
    spawn_clearance = capsule(world, (680, 600, 113), (680, 600, 114))
    if spawn_clearance["hit"]: failures.append(f"standing start capsule obstructed: {spawn_clearance}")
    operator_aisle = capsule(world, (680, 600, 113), (680, 4400, 113))
    if operator_aisle["hit"]: failures.append(f"positive-X operator aisle obstructed: {operator_aisle}")
    maintenance_approach = capsule(world, (-680, 4300, 113), (-450, 4650, 113))
    if maintenance_approach["hit"]: failures.append(f"negative-X maintenance approach obstructed: {maintenance_approach}")
    guarded_entry = capsule(world, (680, 4700, 113), (250, 4700, 113))
    if not guarded_entry["hit"]:
        failures.append(f"S07 operator-side guarded entry is physically open: {guarded_entry}")
    query_rows = []
    for actor in query:
        component = actor.get_component_by_class(unreal.StaticMeshComponent)
        enabled = str(component.get_editor_property("body_instance").get_editor_property("collision_enabled")) if component else None
        pawn_response = str(component.get_collision_response_to_channel(unreal.CollisionChannel.ECC_PAWN)) if component else None
        row = {"actor": actor.get_actor_label(), "collision_enabled": enabled,
               "pawn_response": pawn_response,
               "physically_blocks_pawn": bool(pawn_response and "BLOCK" in pawn_response.upper())}
        if not component or "QUERY_ONLY" not in (enabled or "").upper() or row["physically_blocks_pawn"]:
            failures.append(f"runtime query mover policy mismatch: {row}")
        query_rows.append(row)

    nav_bounds = next((actor for actor in actors if isinstance(actor, unreal.NavMeshBoundsVolume)), None)
    nav = unreal.NavigationSystemV1.get_navigation_system(world)
    if nav and nav_bounds:
        nav.on_navigation_bounds_updated(nav_bounds)
    return failures, {"pawn": pawn_row, "floor_trace": floor_trace,
                      "spawn_capsule_clearance": spawn_clearance,
                      "operator_aisle_capsule_sweep": operator_aisle,
                      "maintenance_approach_capsule_sweep": maintenance_approach,
                      "operator_side_guarded_entry_sweep": guarded_entry,
                      "query_mover_rows": query_rows}, nav


def sample_robot(world):
    actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.StaticMeshActor)
    robot = [actor for actor in actors
             if any(value.startswith("LB.PressTrain.Role.unload_robot_") for value in actor_tags(actor))]
    for actor in robot:
        origin, extent = actor.get_actor_bounds(False, False)
        for axis, value in enumerate((origin.x - extent.x, origin.y - extent.y, origin.z - extent.z)):
            robot_bounds_min[axis] = min(robot_bounds_min[axis], value)
        for axis, value in enumerate((origin.x + extent.x, origin.y + extent.y, origin.z + extent.z)):
            robot_bounds_max[axis] = max(robot_bounds_max[axis], value)
        for other in actor.get_overlapping_actors():
            if "LB.Collision.TrainA.Blocking.v018" in actor_tags(other):
                overlap_pairs.add((actor.get_actor_label(), other.get_actor_label()))


def tick(_delta):
    global phase, phase_started, initial_evidence
    try:
        now = time.monotonic()
        if now - started > 55.0:
            finish([f"physical PIE timeout in phase {phase}"])
            return
        world = unreal.EditorLevelLibrary.get_game_world()
        if world is None:
            return
        if phase == "wait_world" and now - phase_started >= 4.0:
            failures, evidence, nav = initial_checks(world)
            initial_evidence = evidence
            initial_evidence["navigation_system_present"] = nav is not None
            if failures:
                finish(failures); return
            phase = "wait_navigation"; phase_started = now; return
        if phase == "wait_navigation":
            if unreal.NavigationSystemV1.is_navigation_being_built_or_locked(world) and now - phase_started < 15.0:
                return
            start = unreal.NavigationSystemV1.project_point_to_navigation(
                world, unreal.Vector(680, 600, 25), None, None, unreal.Vector(100, 100, 220))
            end = unreal.NavigationSystemV1.project_point_to_navigation(
                world, unreal.Vector(680, 4400, 25), None, None, unreal.Vector(100, 100, 220))
            nav_row = {"projected_start_cm": [start.x, start.y, start.z] if start else None,
                       "projected_end_cm": [end.x, end.y, end.z] if end else None}
            failures = []
            path = unreal.NavigationSystemV1.find_path_to_location_synchronously(world, start, end) if start and end else None
            nav_row.update({"path_present": path is not None,
                            "path_valid": path.is_valid() if path else False,
                            "path_partial": path.is_partial() if path else None,
                            "path_length_cm": path.get_path_length() if path else None,
                            "path_points_cm": [[point.x, point.y, point.z] for point in path.path_points] if path else []})
            if not start or not end or not path or not path.is_valid() or path.is_partial():
                failures.append(f"operator aisle navigation path failed: {nav_row}")
            initial_evidence["operator_aisle_navigation"] = nav_row
            if failures:
                finish(failures); return
            stations = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBPressTrainAStation)
            if len(stations) != 1:
                finish([f"expected one runtime authority, found {len(stations)}"]); return
            station = stations[0]
            station.set_access_interlocks_closed(True); station.set_safety_circuit_healthy(True)
            station.set_emergency_stop_active(False); station.set_destack_healthy(True)
            station.set_transfer_healthy(True); station.set_hydraulic_pressure(280.0)
            station.set_press_load(45.0); station.set_inspection_healthy(True)
            station.set_stillage_output_clear(True); station.set_target_strokes_per_minute(10.0)
            if not station.queue_reserved_blank(unreal.Name("PTA-PHYS-001"), unreal.Name("PR010-PHYS-001")):
                finish(["physical validator reserved blank refused"]); return
            if not station.execute_remote_command(unreal.LBPressTrainACommand.POWER_ON, SOURCE, AUTHORITY):
                finish(["physical validator power on refused"]); return
            if not station.execute_remote_command(unreal.LBPressTrainACommand.START, SOURCE, AUTHORITY):
                finish(["physical validator start refused"]); return
            phase = "sample_cycle"; phase_started = now; return
        if phase == "sample_cycle":
            sample_robot(world)
            station = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBPressTrainAStation)[0]
            status = station.get_hmi_status()
            if status.good_panels < 1 and now - phase_started < 18.0:
                return
            allowed = []
            unexpected = []
            for robot_actor, blocker in sorted(overlap_pairs):
                reason = None
                if "RobotBase" in robot_actor and "Foundation" in blocker:
                    reason = "robot base anchored to foundation"
                elif "RuntimeRobot" in blocker:
                    reason = "robot hierarchy self-interface"
                elif any(token in blocker for token in ("TransferRail", "Inspect", "Stillage")):
                    reason = "engineered S07 transfer/inspection/stillage interface"
                row = {"robot_actor": robot_actor, "blocking_actor": blocker}
                if reason: row["allowed_reason"] = reason; allowed.append(row)
                else: unexpected.append(row)
            failures = []
            if status.good_panels < 1: failures.append("cycle did not complete while sampling robot sweep")
            if unexpected: failures.append(f"unexpected robot/blocker overlaps: {unexpected}")
            finish(failures, {"cycle_good_panels": status.good_panels,
                              "allowed_robot_blocker_contacts": allowed,
                              "unexpected_robot_blocker_overlaps": unexpected})
    except Exception as exc:
        finish([f"validator exception: {type(exc).__name__}: {exc}"])


handle = unreal.register_slate_post_tick_callback(tick)
