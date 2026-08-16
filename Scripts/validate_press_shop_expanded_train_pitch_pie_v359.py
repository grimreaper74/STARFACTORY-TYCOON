"""Read-only PIE validation of the v356 expanded four-train layout.

Tests player navigation and direct aisle clearance.  The service-equipment box
is a conservative gameplay probe only; it is not an engineering certification.
The candidate map is never saved by this script.
"""
from datetime import datetime, timezone
import json
from pathlib import Path
import time

import unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP = "/Game/LineBoss/Maps/LB_PressShop_ExpandedTrainPitchCandidate_v356"
ROOT = Path(unreal.Paths.project_dir())
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_expanded_train_pitch_pie_v360.json"
LEVELS = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not LEVELS.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
OUT.parent.mkdir(parents=True, exist_ok=True)

# Midpoints of the three 8.435 m clear inter-train aisles.
AISLES = {"A_B": -3200.0, "B_C": -1000.0, "C_D": 1200.0}
TARGET_CENTRES = {"A": -4300.0, "B": -2100.0, "C": 100.0, "D": 2300.0}
unreal.EditorLevelLibrary.editor_play_simulate()
started = time.monotonic()
phase_started = started
phase = "wait_world"
handle = None


def v3(value):
    return [round(value.x, 3), round(value.y, 3), round(value.z, 3)] if value else None


def actor_train(actor):
    values = {str(tag) for tag in actor.tags}
    for train in "ABCD":
        if f"LB.PressTrain.Installed.TRAIN_{train}" in values:
            return train
    return None


def nav_route(world, y):
    request_a = unreal.Vector(900.0, y, 25.0)
    request_b = unreal.Vector(6750.0, y, 25.0)
    extent = unreal.Vector(175.0, 175.0, 250.0)
    a = unreal.NavigationSystemV1.project_point_to_navigation(world, request_a, None, None, extent)
    b = unreal.NavigationSystemV1.project_point_to_navigation(world, request_b, None, None, extent)
    path = unreal.NavigationSystemV1.find_path_to_location_synchronously(world, a, b) if a and b else None
    return {
        "requested_start_cm": v3(request_a), "requested_end_cm": v3(request_b),
        "projected_start_cm": v3(a), "projected_end_cm": v3(b),
        "path_present": path is not None,
        "path_valid": bool(path and path.is_valid()),
        "path_partial": path.is_partial() if path else None,
        "path_length_cm": round(path.get_path_length(), 3) if path else None,
        "path_points_cm": [v3(point) for point in path.path_points] if path else [],
    }


def direct_capsule(world, y):
    start = unreal.Vector(900.0, y, 113.0)
    end = unreal.Vector(6750.0, y, 113.0)
    result = unreal.SystemLibrary.capsule_trace_single(
        world, start, end, 34.0, 87.0,
        unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [],
        unreal.DrawDebugTrace.NONE, True)
    hit, data = result
    return {
        "clear": not hit,
        "hit_actor": data.hit_actor.get_actor_label() if hit and data.hit_actor else None,
        "hit_location_cm": v3(data.location) if hit else None,
    }


def finish(payload):
    global handle
    payload.update({
        "$schema": "cairnwell/audit/press-shop-expanded-train-pitch-pie-v359/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "map": MAP, "map_saved": False, "promotion_authorized": False,
        "engineering_clearance_certified": False,
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
    if now - started > 180.0:
        finish({"status": "FAIL__TIMEOUT", "phase": phase})
        return
    world = unreal.EditorLevelLibrary.get_game_world()
    if world is None:
        return
    if phase == "wait_world":
        if now - phase_started < 5.0:
            return
        nav = unreal.NavigationSystemV1.get_navigation_system(world)
        if nav:
            for bounds in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.NavMeshBoundsVolume):
                nav.on_navigation_bounds_updated(bounds)
        phase = "wait_navigation"
        phase_started = now
        return
    if phase == "wait_navigation":
        if unreal.NavigationSystemV1.is_navigation_being_built_or_locked(world) and now - phase_started < 125.0:
            return
        authorities = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBPressTrainAStation)
        authority_rows = []
        failures = []
        for actor in authorities:
            train = actor_train(actor)
            if train:
                location = actor.get_actor_location()
                authority_rows.append({"train": train, "actor": actor.get_actor_label(), "location_cm": v3(location)})
                if abs(location.y - TARGET_CENTRES[train]) > 5.0:
                    failures.append(f"Train {train} authority Y {location.y:.1f} != {TARGET_CENTRES[train]:.1f}")
        authority_rows.sort(key=lambda row: row["train"])
        if len(authority_rows) != 4:
            failures.append(f"expected four train authorities, found {len(authority_rows)}")
        aisle_rows = {}
        for name, y in AISLES.items():
            route = nav_route(world, y)
            capsule = direct_capsule(world, y)
            aisle_rows[name] = {"centre_y_cm": y, "player_navigation": route, "direct_standing_capsule": capsule}
            if not route["path_valid"] or route["path_partial"]:
                failures.append(f"{name} player navigation failed")
        finish({
            "status": "PASS__EXPANDED_AISLES_NAVIGABLE__DIRECT_COLUMN_CONSTRAINTS_RECORDED__NOT_PROMOTED" if not failures else "FAIL__EXPANDED_LAYOUT_FUNCTIONAL_GATE",
            "centre_pitch_cm": 2200.0,
            "completed_visual_clear_gap_cm": 843.5,
            "authorities": authority_rows,
            "aisles": aisle_rows,
            "failures": failures,
            "interpretation": "Navigation proves player connectivity. Direct capsule hits identify columns or other obstructions but do not fail a valid routed path. Die carts and bins require a separate gameplay-envelope sweep before promotion.",
        })


handle = unreal.register_slate_post_tick_callback(tick)
