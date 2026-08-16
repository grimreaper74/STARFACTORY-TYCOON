"""PIE support-robot navigation proof around PR-010 protected process space."""

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import unreal


unreal.EditorPythonScripting.set_keep_python_script_alive(True)
ROOT = Path(unreal.Paths.project_dir())
TARGET_MAP = "/Game/LineBoss/Maps/LB_PressShop_PR010CollisionNavigationCandidate_v099"
OUT = ROOT / "Saved/Audits/PR010_CollisionNavigation/navigation_pie_audit_v099.json"
PROTECTED = {"x": [930.0, 1770.0], "y": [-2700.0, -1300.0]}
ROUTES = {
    "south_service_robot_route": {
        "start": unreal.Vector(1000.0, -2920.0, 30.0),
        "end": unreal.Vector(1900.0, -2920.0, 30.0),
        "minimum_length_cm": 900.0,
    },
    "north_service_robot_route": {
        "start": unreal.Vector(1000.0, -1080.0, 30.0),
        "end": unreal.Vector(1900.0, -1080.0, 30.0),
        "minimum_length_cm": 900.0,
    },
    "east_vehicle_handoff_route": {
        "start": unreal.Vector(1900.0, -2920.0, 30.0),
        "end": unreal.Vector(1900.0, -1080.0, 30.0),
        "minimum_length_cm": 1840.0,
    },
}

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not levels.load_level(TARGET_MAP): raise RuntimeError(TARGET_MAP)
unreal.EditorLevelLibrary.editor_play_simulate()
started = time.monotonic()
handle = None


def point_row(point): return [float(point.x), float(point.y), float(point.z)]
def inside(point): return PROTECTED["x"][0] < point.x < PROTECTED["x"][1] and PROTECTED["y"][0] < point.y < PROTECTED["y"][1]


def finish(routes, failures):
    global handle
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    payload = {
        "$schema": "cairnwell/audit/pr010-navigation-pie-v099/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "target_map": TARGET_MAP,
        "status": "PASS__PR010_V099_THREE_NONPARTIAL_ROBOT_ROUTES_AVOID_PROTECTED_BUFFER__NOT_PROMOTED" if not failures else "FAIL__PR010_V099_NAVIGATION__NOT_PROMOTED",
        "protected_process_space_cm": PROTECTED,
        "routes": routes,
        "failures": failures,
        "promotion_authorized": False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if failures: unreal.log_error(f"CAIRNWELL_PR010_NAV_FAIL {failures}")
    else: unreal.log(f"CAIRNWELL_PR010_NAV_PASS {OUT}")
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()


def tick(_delta):
    if time.monotonic() - started > 75.0:
        finish({}, ["timeout waiting for navigation"]); return
    if time.monotonic() - started < 5.0: return
    world = unreal.EditorLevelLibrary.get_game_world()
    if world is None: return
    bootstraps = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBPressShopNavigationBootstrap)
    if len(bootstraps) != 1:
        finish({}, [f"expected one navigation bootstrap, found {len(bootstraps)}"]); return
    bootstrap = bootstraps[0]
    if not bootstrap.is_navigation_ready(): return
    rows, failures = {}, []
    for name, contract in ROUTES.items():
        valid = bool(bootstrap.validate_path(contract["start"], contract["end"]))
        partial = bool(bootstrap.is_validated_path_partial()) if valid else None
        length = float(bootstrap.get_validated_path_length()) if valid else None
        points = list(bootstrap.get_validated_path_points()) if valid else []
        protected = [point_row(point) for point in points if inside(point)]
        rows[name] = {
            "start_cm": point_row(contract["start"]), "end_cm": point_row(contract["end"]),
            "path_valid": valid, "path_partial": partial, "path_length_cm": length,
            "path_points_cm": [point_row(point) for point in points],
            "protected_point_count": len(protected), "protected_points_cm": protected,
        }
        if not valid or partial: failures.append(f"{name}: invalid or partial")
        elif length < contract["minimum_length_cm"]: failures.append(f"{name}: path too short {length:.2f}")
        if protected: failures.append(f"{name}: entered protected process space")
    finish(rows, failures)


handle = unreal.register_slate_post_tick_callback(tick)
