"""Read-only live-PIE audit of v260 support-fleet dispatch readiness.

This proves runtime certification state and navmesh reachability only.  It does
not certify a route asset, move a robot, or save the protected retained map.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
import time

import unreal


unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v260"
ROOT = Path(unreal.Paths.project_dir())
OUT = ROOT / "Saved/Audits/SupportRobots/press_shop_support_fleet_dispatch_readiness_v260.json"
LEVELS = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not LEVELS.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
OUT.parent.mkdir(parents=True, exist_ok=True)

# Exact retained v260 berth roots.  The open dock portal and robot front face
# world -Y, so decreasing Y is the straight egress direction.
BERTHS = {
    "LB-MR01-01": (-6495.0, 5160.0, 62.5),
    "LB-MR01-02": (-5095.0, 5160.0, 62.5),
    "LB-CR01-01": (-1495.0, 5160.0, 56.0),
    "LB-CR01-02": (-295.0, 5160.0, 56.0),
}

unreal.EditorLevelLibrary.editor_play_simulate()
started = time.monotonic()
phase_started = started
phase = "wait_world"
handle = None


def vec(row):
    return [round(row.x, 3), round(row.y, 3), round(row.z, 3)] if row else None


def tags(actor):
    return {str(value) for value in actor.tags}


def unit_id(actor):
    prefix = "LB.SupportRobot.UnitId."
    return next((value[len(prefix):] for value in tags(actor) if value.startswith(prefix)), actor.get_actor_label())


def project(world, location):
    return unreal.NavigationSystemV1.project_point_to_navigation(
        world, unreal.Vector(*location), None, None, unreal.Vector(140.0, 140.0, 240.0))


def path_row(world, start_location, end_location):
    start = project(world, start_location)
    end = project(world, end_location)
    path = unreal.NavigationSystemV1.find_path_to_location_synchronously(world, start, end) if start and end else None
    return {
        "requested_start_cm": list(start_location),
        "requested_end_cm": list(end_location),
        "projected_start_cm": vec(start),
        "projected_end_cm": vec(end),
        "path_present": path is not None,
        "path_valid": bool(path and path.is_valid()),
        "path_partial": path.is_partial() if path else None,
        "path_length_cm": round(path.get_path_length(), 3) if path else None,
        "path_points_cm": [vec(point) for point in path.path_points] if path else [],
    }


def finish(payload):
    global handle
    payload.update({
        "$schema": "cairnwell/audit/press-shop-support-fleet-dispatch-readiness-v260/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "map": MAP,
        "map_saved": False,
        "route_certification_granted": False,
        "promotion_authorized": False,
    })
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.SystemLibrary.quit_editor()


def tick(_delta):
    global phase, phase_started
    now = time.monotonic()
    if now - started > 55.0:
        finish({"status": "FAIL__TIMEOUT", "phase": phase})
        return
    world = unreal.EditorLevelLibrary.get_game_world()
    if world is None:
        return
    if phase == "wait_world":
        if now - phase_started < 4.0:
            return
        nav_bounds = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.NavMeshBoundsVolume)
        nav = unreal.NavigationSystemV1.get_navigation_system(world)
        if nav:
            for bounds in nav_bounds:
                nav.on_navigation_bounds_updated(bounds)
        phase = "wait_navigation"
        phase_started = now
        return
    if phase == "wait_navigation":
        if unreal.NavigationSystemV1.is_navigation_being_built_or_locked(world) and now - phase_started < 18.0:
            return
        robots = (
            unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBMaintenanceAMR)
            + unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBCleaningAMR)
        )
        rows = []
        failures = []
        for robot in sorted(robots, key=unit_id):
            uid = unit_id(robot)
            saved = robot.capture_common_save_state()
            root = BERTHS.get(uid)
            if root is None:
                failures.append(f"unexpected robot identity {uid}")
                continue
            x, y, z = root
            # The robot footprint occupies the dock datum. Start nav proof at
            # the open portal/apron and continue straight to the common aisle.
            apron = (x, y - 170.0, 25.0)
            aisle = (x, 4200.0, 25.0)
            cross_aisle = (-3300.0, 4200.0, 25.0)
            egress = path_row(world, apron, aisle)
            return_leg = path_row(world, aisle, apron)
            shared = path_row(world, aisle, cross_aisle)
            row = {
                "actor": robot.get_actor_label(),
                "unit_id": uid,
                "variant_id": str(saved.variant_id),
                "state": str(saved.state),
                "condition": str(saved.condition),
                "certified": bool(saved.certified),
                "route_revalidation_required": bool(saved.route_revalidation_required),
                "docked": bool(saved.docked),
                "dock_id": str(saved.dock_id),
                "battery_percent": round(saved.battery_state_of_charge_percent, 3),
                "actor_location_cm": vec(robot.get_actor_location()),
                "straight_egress": egress,
                "straight_return": return_leg,
                "shared_service_aisle": shared,
            }
            for route_name, route in (("egress", egress), ("return", return_leg), ("shared", shared)):
                if not route["path_valid"] or route["path_partial"]:
                    failures.append(f"{uid} {route_name} nav path failed")
            rows.append(row)
        if len(rows) != 4:
            failures.append(f"expected four retained robots, found {len(rows)}")
        nav_pass = not any("nav path failed" in item for item in failures)
        all_certified = len(rows) == 4 and all(row["certified"] and not row["route_revalidation_required"] for row in rows)
        status = (
            "PASS__FOUR_BERTH_NAV_CORRIDORS_AND_RUNTIME_CERTIFICATION_READY__NO_ROUTE_GRANTED"
            if not failures and all_certified else
            "PASS__FOUR_BERTH_NAV_CORRIDORS__COMMISSIONING_REQUIRED__NO_ROUTE_GRANTED"
            if not failures and nav_pass else
            "FAIL__DISPATCH_READINESS"
        )
        finish({
            "status": status,
            "runtime_robot_count": len(rows),
            "navigation_corridors_pass": nav_pass,
            "all_robots_runtime_certified": all_certified,
            "robots": rows,
            "failures": failures,
            "interpretation": (
                "Navmesh reachability is necessary but never certifies a support-robot route. "
                "A fresh child may define route assets only after these exact corridors pass."
            ),
        })


handle = unreal.register_slate_post_tick_callback(tick)
