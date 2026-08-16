"""PIE proof for the v095 shell boundary, clear material portals and interlocked service door."""

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from press_shop_pr009_enclosure_release_v095_config import TARGET_MAP


unreal.EditorPythonScripting.set_keep_python_script_alive(True)
ROOT = Path(unreal.Paths.project_dir())
OUT = ROOT / "Saved/Audits/PR009_InMap_v095/enclosure_physical_pie_audit.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not levels.load_level(TARGET_MAP):
    raise RuntimeError(TARGET_MAP)
unreal.EditorLevelLibrary.editor_play_simulate()
started = time.monotonic()
opened_at = None
handle = None
closed_rows = None
station = None


def hit_labels(results):
    labels = []
    for result in results or []:
        fields = result.to_tuple()
        if not fields[0]: continue
        actor = fields[9]
        if actor: labels.append(actor.get_actor_label())
    return labels


def line(world, start, end):
    results = unreal.SystemLibrary.line_trace_multi(
        world, unreal.Vector(*start), unreal.Vector(*end), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
        False, [], unreal.DrawDebugTrace.NONE, True)
    labels = hit_labels(results)
    return {"start_cm": start, "end_cm": end, "hit_labels": labels,
            "enclosure_hits": [label for label in labels if "V095_ENC_SM_" in label]}


def box(world, start, end, half):
    results = unreal.SystemLibrary.box_trace_multi(
        world, unreal.Vector(*start), unreal.Vector(*end), unreal.Vector(*half), unreal.Rotator(),
        unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [], unreal.DrawDebugTrace.NONE, True)
    labels = hit_labels(results)
    return {"start_cm": start, "end_cm": end, "half_extent_cm": half, "hit_labels": labels,
            "enclosure_hits": [label for label in labels if "V095_ENC_SM_" in label]}


def finish(open_door_row, failures):
    global handle
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    payload = {
        "$schema": "cairnwell/audit/pr009-enclosure-physical-pie-v095/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "target_map": TARGET_MAP,
        "status": "PASS__SHELL_BOUNDARY_PORTALS_AND_INTERLOCKED_DOOR__NOT_PROMOTED" if not failures else "FAIL__NOT_PROMOTED",
        "closed_state": closed_rows,
        "open_service_door": open_door_row,
        "failures": failures,
        "promotion_authorized": False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    unreal.log(f"PR009_V095_ENCLOSURE_PHYSICAL_{'PASS' if not failures else 'FAIL'} output={OUT}")
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()


def tick(_delta):
    global opened_at, closed_rows, station
    elapsed = time.monotonic() - started
    world = unreal.EditorLevelLibrary.get_game_world()
    if world is None or elapsed < 4.0:
        return
    if opened_at is None:
        stations = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBPR009Station)
        if len(stations) != 1:
            finish({}, [f"expected one PR-009 station, found {len(stations)}"])
            return
        station = stations[0]
        closed_rows = {
            "south_wall": line(world, (700.0, -2500.0, 170.0), (700.0, -2100.0, 170.0)),
            "north_wall": line(world, (700.0, -1500.0, 170.0), (700.0, -1900.0, 170.0)),
            "roof": line(world, (600.0, -2000.0, 500.0), (600.0, -2000.0, 300.0)),
            "closed_service_door": line(world, (481.0, -2500.0, 170.0), (481.0, -2100.0, 170.0)),
            "full_blank_portal_sweep": box(world, (180.0, -2000.0, 105.0), (1020.0, -2000.0, 105.0), (130.0, 90.0, 0.25)),
        }
        station.set_guards_closed(False)
        opened_at = time.monotonic()
        return
    if time.monotonic() - opened_at < 1.5:
        return
    open_row = line(world, (481.0, -2500.0, 170.0), (481.0, -2100.0, 170.0))
    open_row["service_door_angle_degrees"] = station.get_service_door_angle_degrees()
    failures = []
    for key in ("south_wall", "north_wall", "roof"):
        if not closed_rows[key]["enclosure_hits"]:
            failures.append(f"{key} does not physically hit the enclosure")
    if not any("ServiceDoor" in label for label in closed_rows["closed_service_door"]["enclosure_hits"]):
        failures.append("closed service-door trace does not hit the authored door")
    if closed_rows["full_blank_portal_sweep"]["enclosure_hits"]:
        failures.append("full 2600 x 1800 mm blank sweep contacts the enclosure portal")
    if any("ServiceDoor" in label for label in open_row["enclosure_hits"]):
        failures.append("open service-door trace still contacts the door")
    if abs(open_row["service_door_angle_degrees"] - 105.0) > 0.1:
        failures.append(f"service door did not reach 105 degrees: {open_row['service_door_angle_degrees']}")
    station.set_guards_closed(True)
    finish(open_row, failures)


handle = unreal.register_slate_post_tick_callback(tick)
