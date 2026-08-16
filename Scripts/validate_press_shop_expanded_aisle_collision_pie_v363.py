"""Read-only PIE collision clearance for v362 expanded inter-train aisles.

The service box is a conservative gameplay probe (6 m long, 3 m wide,
2 m high), not a verified real die-cart or an engineering certification.
"""
from datetime import datetime, timezone
import json
from pathlib import Path
import time
import unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP = "/Game/LineBoss/Maps/LB_PressShop_ExpandedTrainNavCandidate_v362"
ROOT = Path(unreal.Paths.project_dir())
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_expanded_aisle_collision_pie_v364.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
OUT.parent.mkdir(parents=True, exist_ok=True)

AISLES = {"A_B": -3200.0, "B_C": -1000.0, "C_D": 1200.0}
OFFSETS = (-250.0, -125.0, 0.0, 125.0, 250.0)
unreal.EditorLevelLibrary.editor_play_simulate()
started = time.monotonic()
handle = None


def vec(value):
    return [round(value.x, 3), round(value.y, 3), round(value.z, 3)] if value else None


def capsule(world, y):
    result = unreal.SystemLibrary.capsule_trace_single(
        world, unreal.Vector(1000, y, 113), unreal.Vector(6700, y, 113),
        34.0, 87.0, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [],
        unreal.DrawDebugTrace.NONE, True)
    if result is None:
        return {"clear": True, "hit_actor": None, "hit_location_cm": None}
    fields = result.to_tuple(); hit = bool(fields[0]); actor = fields[9] if hit else None
    return {"clear": not hit, "hit_actor": actor.get_actor_label() if actor else None,
            "hit_location_cm": vec(fields[5]) if hit else None}


def service_box(world, y):
    result = unreal.SystemLibrary.box_trace_single(
        world, unreal.Vector(1000, y, 110), unreal.Vector(6700, y, 110),
        unreal.Vector(300, 150, 100), unreal.Rotator(),
        unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [],
        unreal.DrawDebugTrace.NONE, True)
    if result is None:
        return {"clear": True, "hit_actor": None, "hit_location_cm": None}
    fields = result.to_tuple(); hit = bool(fields[0]); actor = fields[9] if hit else None
    return {"clear": not hit, "hit_actor": actor.get_actor_label() if actor else None,
            "hit_location_cm": vec(fields[5]) if hit else None}


def finish(payload):
    global handle
    payload.update({"$schema": "cairnwell/audit/press-shop-expanded-aisle-collision-pie-v364/v1",
                    "generated_utc": datetime.now(timezone.utc).isoformat(), "map": MAP,
                    "map_saved": False, "promotion_authorized": False,
                    "engineering_clearance_certified": False})
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.SystemLibrary.quit_editor()


def tick(_delta):
    if time.monotonic() - started < 7.0:
        return
    world = unreal.EditorLevelLibrary.get_game_world()
    if world is None:
        return
    rows = {}
    failures = []
    for name, centre in AISLES.items():
        player_lanes = []
        equipment_lanes = []
        for offset in OFFSETS:
            player_lanes.append({"offset_y_cm": offset, **capsule(world, centre + offset)})
            equipment_lanes.append({"offset_y_cm": offset, **service_box(world, centre + offset)})
        player_clear = [row["offset_y_cm"] for row in player_lanes if row["clear"]]
        equipment_clear = [row["offset_y_cm"] for row in equipment_lanes if row["clear"]]
        if not player_clear:
            failures.append(f"{name} has no clear direct standing-player lane")
        if not equipment_clear:
            failures.append(f"{name} has no clear direct conservative service-equipment lane")
        rows[name] = {"centre_y_cm": centre, "player_lanes": player_lanes,
                      "service_equipment_lanes": equipment_lanes,
                      "clear_player_offsets_cm": player_clear,
                      "clear_service_equipment_offsets_cm": equipment_clear}
    finish({
        "status": "PASS__ALL_THREE_EXPANDED_AISLES_HAVE_DIRECT_PLAYER_AND_CONSERVATIVE_SERVICE_LANES__NOT_PROMOTED" if not failures else "FAIL__EXPANDED_AISLE_COLLISION_CLEARANCE",
        "completed_visual_clear_gap_cm": 843.5,
        "standing_player_probe": {"capsule_radius_cm": 34, "capsule_half_height_cm": 87},
        "service_equipment_gameplay_probe": {"full_length_cm": 600, "full_width_cm": 300, "full_height_cm": 200,
            "purpose": "conservative gameplay route probe only; actual equipment dimensions remain TBC"},
        "aisles": rows, "failures": failures,
    })


handle = unreal.register_slate_post_tick_callback(tick)
