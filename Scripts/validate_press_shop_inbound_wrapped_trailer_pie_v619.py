"""Exact-v616 PIE proof for the visible four-coil inbound delivery sequence.

This validator watches the map-authored tagged presentation actors as well as the
native delivery/storage authorities.  It never saves or promotes the map.
"""

from datetime import datetime, timezone
from pathlib import Path
import json
import time

import unreal


unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP = "/Game/LineBoss/Developer/Validation/LB_PressShop_InboundWrappedTrailerCandidate_v616"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/PressShopIntegration/inbound_wrapped_trailer_pie_v619.json"
OUT.parent.mkdir(parents=True, exist_ok=True)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

unreal.EditorLevelLibrary.editor_play_simulate()
started = time.monotonic()
handle = None
next_delivery = 0
last_phase_key = None
phase_history = []
cycle_evidence = []
actor_initial = {}
actor_samples = {}
start_results = []
coil_ids = [f"COIL-INBOUND-V619-{index:03d}" for index in range(1, 5)]
tag_names = {
    "lorry": "LB.Inbound.Visual.Lorry",
    "bridge": "LB.Inbound.Visual.CraneBridge",
    "trolley": "LB.Inbound.Visual.CraneTrolley",
    "hoist": "LB.Inbound.Visual.Hoist",
    "hook": "LB.Inbound.Visual.Hook",
    "saddle": "LB.Inbound.Visual.Saddle",
    "coil_01": "LB.Inbound.Visual.TrailerCoil.01",
    "coil_02": "LB.Inbound.Visual.TrailerCoil.02",
    "coil_03": "LB.Inbound.Visual.TrailerCoil.03",
    "coil_04": "LB.Inbound.Visual.TrailerCoil.04",
}


def one(world, cls):
    rows = unreal.GameplayStatics.get_all_actors_of_class(world, cls)
    return rows[0] if len(rows) == 1 else None


def actor_with_tag(world, tag):
    rows = unreal.GameplayStatics.get_all_actors_with_tag(world, tag)
    return rows[0] if len(rows) == 1 else None


def vec(actor):
    location = actor.get_actor_location()
    return [round(location.x, 2), round(location.y, 2), round(location.z, 2)]


def hidden(actor):
    try:
        return bool(actor.is_hidden())
    except Exception:
        return bool(actor.get_editor_property("hidden"))


def distance(a, b):
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2) ** 0.5


def finish(status, failures=None, extra=None):
    global handle
    failures = failures or []
    payload = {
        "$schema": "cairnwell/audit/press-shop-inbound-wrapped-trailer-pie-v619/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "map": MAP,
        "status": status,
        "coil_ids": coil_ids,
        "start_results": start_results,
        "phase_history": phase_history,
        "cycle_evidence": cycle_evidence,
        "actor_initial": actor_initial,
        "actor_samples": actor_samples,
        "failures": failures,
        "promotion_authorized": False,
    }
    if extra:
        payload.update(extra)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    unreal.log(f"LB_INBOUND_WRAPPED_TRAILER_V619_{'PASS' if not failures else 'FAIL'}::{json.dumps(payload)}")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()


def tick(_delta):
    global next_delivery, last_phase_key
    try:
        elapsed = time.monotonic() - started
        world = unreal.EditorLevelLibrary.get_game_world()
        if not world:
            return

        delivery = one(world, unreal.LBInboundDeliveryController)
        agv = one(world, unreal.LBCoilAGVController)
        stores = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBPressShopStorageZone)
        store = next((s for s in stores if str(s.get_zone_id()) == "SZ-COIL-PR003"), None)
        actors = {name: actor_with_tag(world, tag) for name, tag in tag_names.items()}

        missing = [name for name, actor in actors.items() if actor is None]
        if not delivery or not agv or not store or missing:
            if elapsed > 15.0:
                finish("FAIL__EXACT_RUNTIME_AUTHORITY_OR_TAG_BINDING", [
                    f"delivery={bool(delivery)} agv={bool(agv)} store={bool(store)} missing_tags={missing}"
                ])
            return

        if not actor_initial:
            for name, actor in actors.items():
                actor_initial[name] = {"location": vec(actor), "hidden": hidden(actor)}
            actor_initial["store_occupancy"] = store.get_occupancy()

        phase = str(delivery.get_phase())
        agv_phase = str(agv.get_phase())
        completed = delivery.get_completed_deliveries()
        occupancy = store.get_occupancy()
        active_index = delivery.get_active_visual_coil_index()
        phase_key = (phase, agv_phase, completed, occupancy, active_index)
        if phase_key != last_phase_key:
            entry = {
                "elapsed": round(elapsed, 2), "delivery_phase": phase,
                "agv_phase": agv_phase, "completed": completed,
                "store_occupancy": occupancy, "active_visual_coil_index": active_index,
                "lorry": vec(actors["lorry"]), "hook": vec(actors["hook"]),
                "coil_locations": [vec(actors[f"coil_{index:02d}"]) for index in range(1, 5)],
                "coil_hidden": [hidden(actors[f"coil_{index:02d}"]) for index in range(1, 5)],
            }
            phase_history.append(entry)
            actor_samples.setdefault(phase, []).append(entry)
            last_phase_key = phase_key

        if elapsed >= 4.0 and next_delivery < 4 and "IDLE" in phase.upper():
            if completed != next_delivery:
                finish("FAIL__DELIVERY_COUNT_OUT_OF_SEQUENCE", [
                    f"before start {next_delivery + 1}: completed={completed}"
                ])
                return
            result = delivery.start_delivery(coil_ids[next_delivery])
            ok = bool(result[0]) if isinstance(result, tuple) else bool(result)
            reason = str(result[1]) if isinstance(result, tuple) and len(result) > 1 else ""
            start_results.append({"index": next_delivery, "coil_id": coil_ids[next_delivery], "ok": ok, "reason": reason})
            if not ok:
                finish("FAIL__START_DELIVERY_REJECTED", [reason or f"delivery {next_delivery + 1} rejected"])
                return
            next_delivery += 1
            return

        if completed > len(cycle_evidence):
            cycle = completed
            cycle_evidence.append({
                "cycle": cycle,
                "completed_deliveries": completed,
                "store_occupancy": occupancy,
                "coil_hidden": [hidden(actors[f"coil_{index:02d}"]) for index in range(1, 5)],
                "agv_phase": agv_phase,
            })

        if completed == 4 and occupancy == actor_initial["store_occupancy"] + 4 \
                and "IDLE" in phase.upper() and "AWAITING_RELOAD" in agv_phase.upper():
            failures = []
            if not delivery.is_visual_sequence_bound():
                failures.append("native controller did not bind the tagged visual sequence")
            lorry_start = actor_initial["lorry"]["location"]
            lorry_end = vec(actors["lorry"])
            if distance(lorry_start, lorry_end) < 100.0:
                failures.append(f"lorry reverse travel too small: {distance(lorry_start, lorry_end):.1f} cm")
            required_phases = [
                "TRUCK_REVERSE", "DOCK_PROVING", "CRANE_TO_COIL", "HOOK_LOWER",
                "HOOK_ENGAGE", "COIL_LIFT", "CRANE_TO_SADDLE", "COIL_LOWER",
                "SADDLE_RELEASE", "AGV_DISPATCH", "AGV_HANDOFF", "AGV_RETURN",
            ]
            observed = "|".join(item["delivery_phase"].upper() for item in phase_history)
            for required in required_phases:
                if required not in observed:
                    failures.append(f"required visible/runtime phase not observed: {required}")
            final_hidden = [hidden(actors[f"coil_{index:02d}"]) for index in range(1, 5)]
            if final_hidden != [True, True, True, True]:
                failures.append(f"trailer coils not consumed exactly once: {final_hidden}")
            for index in range(1, 5):
                name = f"coil_{index:02d}"
                start_location = actor_initial[name]["location"]
                samples = [entry["coil_locations"][index - 1] for entry in phase_history]
                max_travel = max(distance(start_location, sample) for sample in samples)
                if max_travel < 200.0:
                    failures.append(f"{name} never visibly travelled from trailer: max {max_travel:.1f} cm")
            status = "PASS__EXACT_V616_FOUR_WRAPPED_COILS_VISIBLE_UNLOAD_AND_STORE__NOT_PROMOTED" if not failures \
                else "FAIL__EXACT_V616_VISIBLE_SEQUENCE_V619__NOT_PROMOTED"
            finish(status, failures, {
                "completed_deliveries": completed,
                "store_occupancy": occupancy,
                "lorry_reverse_distance_cm": round(distance(lorry_start, lorry_end), 2),
                "final_coil_hidden": final_hidden,
                "visual_sequence_bound": delivery.is_visual_sequence_bound(),
                "inbound_dock_id": str(delivery.get_inbound_dock_id()),
                "coil_store_id": str(delivery.get_coil_store_id()),
            })
            return

        # One visually readable delivery takes roughly 80-90 seconds at the
        # authored crane/AGV speeds.  Four sequential coils therefore need a
        # wider gate than the former 260 seconds, which expired while the
        # fourth coil was already in CRANE_TO_COIL after three valid handoffs.
        if elapsed > 380.0:
            finish("FAIL__EXACT_V616_FOUR_COIL_SEQUENCE_TIMEOUT", [
                f"phase={phase} agv_phase={agv_phase} completed={completed} occupancy={occupancy} reason={delivery.get_last_reason()}"
            ])
    except Exception as exc:
        finish("FAIL__EXACT_V616_VALIDATOR_EXCEPTION", [f"{type(exc).__name__}: {exc}"])


handle = unreal.register_slate_post_tick_callback(tick)
