"""PIE proof that the v102 map's native PR-010 station drives its bound HMI text."""

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import unreal


unreal.EditorPythonScripting.set_keep_python_script_alive(True)
ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR010ReleaseArtCandidate_v102"
OUT = ROOT / "Saved/Audits/PR010_ReleaseArt_v102/live_hmi_pie_audit_v102.json"
AUTHORITY = unreal.Name("CW.MW.CONTROL_ROOM")
SOURCE = unreal.Name("PR010_V102_LIVE_HMI_GATE")
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
unreal.EditorLevelLibrary.editor_play_simulate()
started = time.monotonic()
handle = None
station = None
state_actor = None
capacity_actor = None
offered = 0
samples = []


def actor_text(actor):
    return str(actor.text_render.get_editor_property("text")) if actor else ""


def finish(failures):
    global handle
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    status = station.get_hmi_status() if station else None
    final_state = actor_text(state_actor)
    final_capacity = actor_text(capacity_actor)
    if "RESERVATION WAIT" not in final_state.upper():
        failures.append(f"bound state text did not reach reservation wait: {final_state}")
    if "3 / 8 STACK POSITIONS" not in final_capacity.upper():
        failures.append(f"bound capacity text did not reach three stacks: {final_capacity}")
    payload = {
        "$schema": "cairnwell/audit/pr010-live-hmi-pie-v102/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "target_map": MAP,
        "status": "PASS__PR010_V102_MAP_BOUND_HMI_STATE_CAPACITY_LIVE__NOT_PROMOTED" if not failures else "FAIL__PR010_V102_LIVE_HMI__NOT_PROMOTED",
        "samples": samples,
        "final_runtime_status": str(status.state) if status else None,
        "final_stored": status.total_stacks_stored if status else None,
        "final_state_text": final_state,
        "final_capacity_text": final_capacity,
        "failures": failures,
        "promotion_authorized": False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()


def tick(_delta):
    global station, state_actor, capacity_actor, offered
    if time.monotonic() - started > 45.0:
        finish(["runtime timeout"])
        return
    if time.monotonic() - started < 3.0:
        return
    world = unreal.EditorLevelLibrary.get_game_world()
    if world is None:
        return
    if station is None:
        stations = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBPR010Station)
        if len(stations) != 1:
            return
        station = stations[0]
        all_actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
        state_actor = next((actor for actor in all_actors if actor.get_actor_label() == "LB_PR010_V101_TEXT_State"), None)
        capacity_actor = next((actor for actor in all_actors if actor.get_actor_label() == "LB_PR010_V101_TEXT_Capacity"), None)
        if state_actor is None or capacity_actor is None:
            finish(["map-bound HMI text actors missing in PIE"])
            return
        station.configure_healthy_inputs()
        if not station.execute_remote_command(unreal.LBPR010Command.POWER_ON, SOURCE, AUTHORITY):
            finish(["trusted power command rejected"])
            return
        if not station.execute_remote_command(unreal.LBPR010Command.START, SOURCE, AUTHORITY):
            finish(["trusted start command rejected"])
            return
    status = station.get_hmi_status()
    samples.append({"state": actor_text(state_actor), "capacity": actor_text(capacity_actor), "stored": status.total_stacks_stored})
    state = str(status.state).upper()
    if "RESERVATION_WAIT" in state and str(status.inbound_stack_id).upper() in ("", "NONE") and offered < 3:
        offered += 1
        if not station.offer_upstream_stack(unreal.Name(f"PR009-STACK-V102-HMI-{offered:02d}"), False):
            finish([f"stack offer {offered} rejected"])
            return
    if status.total_stacks_stored >= 3 and "RESERVATION_WAIT" in state:
        finish([])


handle = unreal.register_slate_post_tick_callback(tick)
