"""PIE navigation proof around PR-009 and exclusion from protected process space."""

import json
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
OUT = ROOT / "Saved" / "Audits" / f"PR009_InMap_{VERSION}" / "navigation_pie_audit.json"

# Station envelope in v084 is world X [220, 980], Y [-2260, -1740]. The
# protected rectangle includes a 20 cm inward tolerance to avoid boundary noise.
PROTECTED = {"x": [240.0, 960.0], "y": [-2240.0, -1760.0]}
ROUTES = {
    "guarded_cell_perimeter": {
        "start": unreal.Vector(80.0, -2460.0, 30.0),
        "end": unreal.Vector(1120.0, -2460.0, 30.0),
        "minimum_length_cm": 1040.0,
    },
    # Validate the opposite service perimeter as well. The cell centreline is
    # deliberately not used as an endpoint: its west side is occupied by the
    # protected PR-008/PR-009 transfer interface and is correctly non-walkable.
    "guarded_cell_north_perimeter": {
        "start": unreal.Vector(80.0, -1540.0, 30.0),
        "end": unreal.Vector(1120.0, -1540.0, 30.0),
        "minimum_length_cm": 1040.0,
    },
}

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not levels.load_level(TARGET_MAP):
    raise RuntimeError(f"Could not load {TARGET_MAP}")
unreal.EditorLevelLibrary.editor_play_simulate()
started = time.monotonic()
handle = None


def point_row(point):
    return [float(point.x), float(point.y), float(point.z)]


def inside_protected(point):
    return PROTECTED["x"][0] < point.x < PROTECTED["x"][1] and PROTECTED["y"][0] < point.y < PROTECTED["y"][1]


def finish(routes, failures):
    global handle
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    payload = {
        "$schema": "cairnwell/audit/press-shop-pr009-navigation-pie/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "target_map": TARGET_MAP,
        "target_version": VERSION,
        "status": "PASS__NOT_PROMOTED" if not failures else "FAIL__NOT_PROMOTED",
        "protected_process_space_cm": PROTECTED,
        "routes": routes,
        "protected_space_traversal_count": sum(row.get("protected_point_count", 0) for row in routes.values()),
        "failures": failures,
        "promotion_authorized": False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if failures:
        unreal.log_error(f"CAIRNWELL_PR009_NAV_FAIL failures={failures} output={OUT}")
    else:
        unreal.log(f"CAIRNWELL_PR009_NAV_PASS output={OUT}")
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()


def tick(_delta_seconds):
    elapsed = time.monotonic() - started
    if elapsed > 60.0:
        finish({}, ["timeout waiting for navigation"])
        return
    if elapsed < 4.0:
        return
    world = unreal.EditorLevelLibrary.get_game_world()
    if world is None:
        return
    bootstraps = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBPressShopNavigationBootstrap)
    if len(bootstraps) != 1:
        finish({}, [f"Expected one navigation bootstrap; found {len(bootstraps)}"])
        return
    bootstrap = bootstraps[0]
    rows = {}
    failures = []
    try:
        for name, contract in ROUTES.items():
            valid = bool(bootstrap.validate_path(contract["start"], contract["end"]))
            length = float(bootstrap.get_validated_path_length()) if valid else None
            points = list(bootstrap.get_validated_path_points()) if valid else []
            protected_points = [point_row(point) for point in points if inside_protected(point)]
            row = {
                "start_cm": point_row(contract["start"]),
                "end_cm": point_row(contract["end"]),
                "path_valid": valid,
                "path_partial": False if valid else None,
                "path_length_cm": length,
                "path_points_cm": [point_row(point) for point in points],
                "protected_point_count": len(protected_points),
                "protected_points_cm": protected_points,
            }
            rows[name] = row
            if not valid:
                failures.append(f"{name}: native path invalid or partial")
            elif length < contract["minimum_length_cm"]:
                failures.append(f"{name}: path length {length:.2f} below endpoint distance")
            if protected_points:
                failures.append(f"{name}: navigation enters protected process space at {len(protected_points)} path points")
        finish(rows, failures)
    except Exception as exc:
        finish(rows, [f"navigation API exception: {exc}"])


handle = unreal.register_slate_post_tick_callback(tick)
