"""Exact-map PIE proof for one identified inbound coil and return-to-ready cycle."""
from datetime import datetime, timezone
from pathlib import Path
import json
import time
import unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP = "/Game/LineBoss/Developer/Validation/LB_PressShop_InboundFunctionalCandidate_v577"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/PressShopIntegration/inbound_functional_cycle_pie_v579.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError("Could not load v577")
OUT.parent.mkdir(parents=True, exist_ok=True)
unreal.EditorLevelLibrary.editor_play_simulate()
started = time.monotonic()
launched = False
history = []
handle = None

def one(world, cls):
    rows = unreal.GameplayStatics.get_all_actors_of_class(world, cls)
    return rows[0] if len(rows) == 1 else None

def finish(status, extra=None):
    global handle
    payload = {
        "$schema": "cairnwell/audit/press-shop-inbound-functional-cycle-pie-v579/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(), "map": MAP,
        "status": status, "phase_history": history, "promotion_authorized": False,
    }
    if extra: payload.update(extra)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.SystemLibrary.quit_editor()

def tick(_delta):
    global launched
    elapsed = time.monotonic() - started
    world = unreal.EditorLevelLibrary.get_game_world()
    if not world:
        return
    delivery = one(world, unreal.LBInboundDeliveryController)
    agv = one(world, unreal.LBCoilAGVController)
    stores = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBPressShopStorageZone)
    store = next((s for s in stores if str(s.get_zone_id()) == "SZ-COIL-PR003"), None)
    if not delivery or not agv or not store:
        if elapsed > 12:
            finish("FAIL__EXACT_AUTHORITY_NOT_UNIQUE_OR_NOT_BOUND")
        return
    phase = str(delivery.get_phase())
    agv_phase = str(agv.get_phase())
    marker = [round(elapsed, 2), phase, agv_phase, delivery.get_completed_deliveries(), store.get_occupancy()]
    if not history or history[-1][1:] != marker[1:]:
        history.append(marker)
    if not launched and elapsed >= 5:
        result = delivery.start_delivery("COIL-INBOUND-TEST-001")
        ok = bool(result[0]) if isinstance(result, tuple) else bool(result)
        reason = str(result[1]) if isinstance(result, tuple) and len(result) > 1 else ""
        history.append([round(elapsed, 2), "START_RESULT", ok, reason])
        if not ok:
            finish("FAIL__START_DELIVERY_REJECTED", {"reason": reason})
            return
        launched = True
    if launched and delivery.get_completed_deliveries() == 1 and store.get_occupancy() == 1 \
            and "IDLE" in phase.upper() and "AWAITING_RELOAD" in agv_phase.upper():
        finish("PASS__ONE_IDENTIFIED_COIL_STORED_AND_AGV_RETURNED_READY__NOT_PROMOTED",
               {"completed_deliveries": 1, "store_occupancy": 1,
                "inbound_dock_id": str(delivery.get_inbound_dock_id()),
                "coil_store_id": str(delivery.get_coil_store_id())})
        return
    if elapsed > 70:
        finish("FAIL__INBOUND_FUNCTIONAL_CYCLE_TIMEOUT",
               {"delivery_phase": phase, "agv_phase": agv_phase,
                "completed_deliveries": delivery.get_completed_deliveries(),
                "store_occupancy": store.get_occupancy(), "last_reason": delivery.get_last_reason()})

handle = unreal.register_slate_post_tick_callback(tick)
