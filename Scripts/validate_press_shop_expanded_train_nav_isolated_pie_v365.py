"""Read-only PIE nav proof for v362 with unrelated nav volumes removed transiently.

The editor map is never saved. This isolates the expanded train block from the
known whole-shop dynamic-nav dirtying cost while preserving exact collision.
"""
from datetime import datetime, timezone
import json
from pathlib import Path
import time
import unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP = "/Game/LineBoss/Maps/LB_PressShop_ExpandedTrainNavCandidate_v362"
TARGET = "LB_PRESS_TRAINS_V362_NavBounds_ExpandedBlock"
ROOT = Path(unreal.Paths.project_dir())
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_expanded_train_nav_isolated_pie_v365.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
removed = []
target_count = 0
for actor in list(actors_api.get_all_level_actors()):
    if not isinstance(actor, unreal.NavMeshBoundsVolume):
        continue
    if actor.get_actor_label() == TARGET:
        target_count += 1
    else:
        removed.append(actor.get_actor_label())
        actors_api.destroy_actor(actor)
if target_count != 1:
    raise RuntimeError(f"Expected one target nav volume, found {target_count}")
OUT.parent.mkdir(parents=True, exist_ok=True)
unreal.EditorLevelLibrary.editor_play_simulate()
started = time.monotonic(); phase_started = started; phase = "wait_world"; handle = None


def vec(value):
    return [round(value.x, 3), round(value.y, 3), round(value.z, 3)] if value else None


def route(world, y):
    extent = unreal.Vector(175, 175, 250)
    requested_a = unreal.Vector(1000, y, 25)
    requested_b = unreal.Vector(6700, y, 25)
    a = unreal.NavigationSystemV1.project_point_to_navigation(world, requested_a, None, None, extent)
    b = unreal.NavigationSystemV1.project_point_to_navigation(world, requested_b, None, None, extent)
    path = unreal.NavigationSystemV1.find_path_to_location_synchronously(world, a, b) if a and b else None
    return {"projected_start_cm": vec(a), "projected_end_cm": vec(b),
            "path_valid": bool(path and path.is_valid()), "path_partial": path.is_partial() if path else None,
            "path_length_cm": round(path.get_path_length(), 3) if path else None,
            "path_points_cm": [vec(point) for point in path.path_points] if path else []}


def finish(payload):
    global handle
    payload.update({"$schema": "cairnwell/audit/press-shop-expanded-train-nav-isolated-pie-v365/v1",
                    "generated_utc": datetime.now(timezone.utc).isoformat(), "map": MAP,
                    "map_saved": False, "transient_removed_nav_volumes": removed,
                    "promotion_authorized": False})
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle); handle = None
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.SystemLibrary.quit_editor()


def tick(_delta):
    global phase, phase_started
    now = time.monotonic()
    if now - started > 120:
        finish({"status": "FAIL__ISOLATED_NAV_TIMEOUT", "phase": phase})
        return
    world = unreal.EditorLevelLibrary.get_game_world()
    if world is None:
        return
    if phase == "wait_world":
        if now - phase_started < 5:
            return
        nav = unreal.NavigationSystemV1.get_navigation_system(world)
        target = next((a for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.NavMeshBoundsVolume)
                       if a.get_actor_label() == TARGET), None)
        if nav and target:
            nav.on_navigation_bounds_updated(target)
        phase = "wait_navigation"; phase_started = now
        return
    if phase == "wait_navigation":
        if unreal.NavigationSystemV1.is_navigation_being_built_or_locked(world) and now - phase_started < 90:
            return
        rows = {name: route(world, y) for name, y in {"A_B": -3200.0, "B_C": -1000.0, "C_D": 1200.0}.items()}
        failures = [f"{name} nav route failed" for name, row in rows.items()
                    if not row["path_valid"] or row["path_partial"]]
        finish({"status": "PASS__THREE_EXPANDED_TRAIN_AISLES_NAVIGABLE_IN_ISOLATED_EXACT_COLLISION__WHOLE_SHOP_NAV_OPTIMIZATION_REMAINS__NOT_PROMOTED" if not failures else "FAIL__ISOLATED_EXPANDED_TRAIN_NAV",
                "routes": rows, "failures": failures,
                "interpretation": "Exact train collision and dedicated coverage pass in isolation. Unrelated whole-shop nav volumes were removed only in memory and no map was saved."})


handle = unreal.register_slate_post_tick_callback(tick)
