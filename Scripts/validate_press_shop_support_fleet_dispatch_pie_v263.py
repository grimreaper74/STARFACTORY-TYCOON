"""Exact live-PIE commissioning and dispatch/return gate for v263."""

from datetime import datetime, timezone
import json
from pathlib import Path
import time

import unreal


unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v263"
ROOT = Path(unreal.Paths.project_dir())
OUT = ROOT / "Saved/Audits/SupportRobots/press_shop_support_fleet_dispatch_pie_v263.json"
UNITS = ("LB-MR01-01", "LB-MR01-02", "LB-CR01-01", "LB-CR01-02")
ROOTS = {
    "LB-MR01-01": (-6495.0, 5160.0, 62.5), "LB-MR01-02": (-5095.0, 5160.0, 62.5),
    "LB-CR01-01": (-1495.0, 5160.0, 56.0), "LB-CR01-02": (-295.0, 5160.0, 56.0),
}
STANDBY = (-3300.0, 3000.0)
LEVELS = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not LEVELS.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
OUT.parent.mkdir(parents=True, exist_ok=True)
unreal.EditorLevelLibrary.editor_play_simulate()
started = time.monotonic()
phase_started = started
phase = "wait_initialisation"
unit_index = 0
rows = []
initial_rows = []
handle = None


def unit_id(robot):
    return str(robot.capture_common_save_state().unit_id)


def location(robot):
    value = robot.get_actor_location()
    return [round(value.x, 3), round(value.y, 3), round(value.z, 3)]


def distance_xy(robot, point):
    value = robot.get_actor_location()
    return ((value.x - point[0]) ** 2 + (value.y - point[1]) ** 2) ** 0.5


def finish(failures):
    global handle
    payload = {
        "$schema": "cairnwell/audit/press-shop-support-fleet-dispatch-pie-v263/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS__FOUR_UNITS_COMMISSIONED_DISPATCHED_AND_RETURNED_TO_CORRECT_DOCKS__NOT_PROMOTED"
                  if not failures else "FAIL__SUPPORT_FLEET_DISPATCH_RUNTIME__NOT_RETAINED",
        "map": MAP,
        "controller_count": 1,
        "initial_fleet": initial_rows,
        "route_cycles": rows,
        "route_revision": 1,
        "runtime_time_dilation_for_test_only": 10.0,
        "map_saved": False,
        "promotion_authorized": False,
        "failures": failures,
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.SystemLibrary.quit_editor()


def tick(_delta):
    global phase, phase_started, unit_index, initial_rows
    now = time.monotonic()
    if now - started > 180.0:
        finish([f"timeout in {phase} for index {unit_index}"])
        return
    world = unreal.EditorLevelLibrary.get_game_world()
    if world is None:
        return
    controllers = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBPressShopSupportFleetController)
    robots = (
        unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBMaintenanceAMR)
        + unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBCleaningAMR)
    )
    by_id = {unit_id(robot): robot for robot in robots}
    if phase == "wait_initialisation":
        if len(controllers) != 1 or len(by_id) != 4 or not controllers[0].is_fleet_ready():
            if now - phase_started > 12.0:
                finish([f"fleet initialization failed controllers={len(controllers)} robots={len(by_id)}"])
            return
        initial_rows = []
        for uid in UNITS:
            robot = by_id[uid]
            saved = robot.capture_common_save_state()
            initial_rows.append({
                "unit_id": uid, "state": str(saved.state), "condition": str(saved.condition),
                "certified": bool(saved.certified),
                "route_revalidation_required": bool(saved.route_revalidation_required),
                "docked": bool(saved.docked), "dock_id": str(saved.dock_id),
                "automatic_charging_route": bool(robot.has_automatic_charging_route()),
                "battery_percent": round(saved.battery_state_of_charge_percent, 3),
            })
        bad = [row["unit_id"] for row in initial_rows if not (
            row["certified"] and not row["route_revalidation_required"] and row["docked"]
            and row["automatic_charging_route"])]
        if bad:
            finish([f"commissioning invariants failed for {bad}"])
            return
        unreal.SystemLibrary.execute_console_command(world, "slomo 10")
        phase = "dispatch"
        phase_started = now
        return

    uid = UNITS[unit_index]
    robot = by_id[uid]
    controller = controllers[0]
    if phase == "dispatch":
        if not controller.dispatch_unit(unreal.Name(uid)):
            finish([f"dispatch command refused for {uid}"])
            return
        rows.append({"unit_id": uid, "dispatch_started_at_cm": location(robot)})
        phase = "wait_standby"
        phase_started = now
        return
    if phase == "wait_standby":
        saved = robot.capture_common_save_state()
        if robot.has_route_authority():
            if now - phase_started > 30.0:
                finish([f"outbound route timeout for {uid}: {location(robot)}"])
            return
        if str(saved.active_fault) not in ("<LBSupportRobotFault.NONE: 0>", "LBSupportRobotFault.NONE"):
            finish([f"outbound route fault for {uid}: {saved.active_fault} {robot.get_last_common_fault_detail()} at {location(robot)}"])
            return
        error = distance_xy(robot, STANDBY)
        rows[-1].update({"standby_location_cm": location(robot), "standby_error_cm": round(error, 3)})
        if error > 15.0:
            finish([f"standby endpoint error for {uid}: {error:.3f} cm"])
            return
        if not controller.return_unit_to_dock(unreal.Name(uid)):
            finish([f"return command refused for {uid}"])
            return
        phase = "wait_dock"
        phase_started = now
        return
    if phase == "wait_dock":
        saved = robot.capture_common_save_state()
        if robot.has_route_authority() or not bool(saved.docked):
            if now - phase_started > 30.0:
                finish([f"return route timeout for {uid}: {location(robot)} state={saved.state} fault={saved.active_fault}"])
            return
        error = distance_xy(robot, ROOTS[uid])
        rows[-1].update({
            "returned_location_cm": location(robot), "dock_error_cm": round(error, 3),
            "dock_id": str(saved.dock_id), "state": str(saved.state),
            "mission_count": int(saved.mission_count),
        })
        if error > 15.0 or str(saved.dock_id) != f"LB-DOCK-{uid[3:]}":
            finish([f"dock endpoint/identity error for {uid}: {error:.3f} cm {saved.dock_id}"])
            return
        unit_index += 1
        if unit_index >= len(UNITS):
            finish([])
            return
        phase = "dispatch"
        phase_started = now


handle = unreal.register_slate_post_tick_callback(tick)
