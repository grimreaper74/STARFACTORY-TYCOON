"""Exercise v269 support-fleet dispatch through the player-facing operations console."""

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import unreal


unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v269"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/ControlRoom/control_room_support_fleet_pie_v269.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
unreal.EditorLevelLibrary.editor_play_simulate()
started = time.monotonic()
phase = "wait_ready"
selected = ""
handle = None


def finish(status, failure=None, evidence=None):
    global handle
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    payload = {
        "$schema": "cairnwell/audit/control-room-support-fleet-pie-v269/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "map": MAP,
        "duration_seconds": time.monotonic() - started,
        "evidence": evidence or {},
        "failure": failure,
        "promotion_authorized": False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    (unreal.log_error if failure else unreal.log)(
        f"LINE_BOSS_CONTROL_ROOM_SUPPORT_FLEET_V269 {'FAIL ' + failure if failure else 'PASS'}")
    unreal.SystemLibrary.quit_editor()


def tick(_delta):
    global phase, selected
    if time.monotonic() - started > 165.0:
        finish("CONTROL_ROOM_SUPPORT_FLEET_V269_FAIL__NOT_PROMOTED", f"timeout in {phase}")
        return
    world = unreal.EditorLevelLibrary.get_game_world()
    if not world:
        return
    consoles = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBControlRoomOperationsConsole)
    if len(consoles) != 1:
        return
    console = consoles[0]
    fleet = console.get_bound_support_fleet()
    if not fleet or not fleet.is_fleet_ready():
        return
    selected = str(console.get_selected_support_unit_id())
    state = fleet.get_unit_snapshot(unreal.Name(selected))
    if not state or str(state.unit_id) != selected:
        finish("CONTROL_ROOM_SUPPORT_FLEET_V269_FAIL__NOT_PROMOTED", "selected unit snapshot unavailable")
        return

    if phase == "wait_ready":
        if selected != "LB-CR01-01" or not state.docked:
            finish("CONTROL_ROOM_SUPPORT_FLEET_V269_FAIL__NOT_PROMOTED", "unexpected initial selection/state")
            return
        if not console.dispatch_selected_support_unit():
            finish("CONTROL_ROOM_SUPPORT_FLEET_V269_FAIL__NOT_PROMOTED", "console dispatch rejected")
            return
        phase = "wait_outbound"
        return
    if phase == "wait_outbound" and not state.docked and not state.route_revalidation_required:
        robot = next((r for r in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBSupportRobot)
                      if str(r.capture_common_save_state().unit_id) == selected), None)
        if robot and not robot.has_route_authority():
            if not console.recall_selected_support_unit():
                finish("CONTROL_ROOM_SUPPORT_FLEET_V269_FAIL__NOT_PROMOTED", "console recall rejected")
                return
            phase = "wait_return"
        return
    if phase == "wait_return" and state.docked and not state.route_revalidation_required:
        console.cycle_support_unit()
        next_id = str(console.get_selected_support_unit_id())
        valid = next_id == "LB-CR01-02" and state.mission_count == 2
        finish(
            "CONTROL_ROOM_SUPPORT_FLEET_V269_DISPATCH_RECALL_AND_SELECTION_PASS__NOT_PROMOTED" if valid
            else "CONTROL_ROOM_SUPPORT_FLEET_V269_FAIL__NOT_PROMOTED",
            None if valid else "selection or mission-count contract mismatch",
            {"bound_fleet": True, "dispatched_unit": selected, "next_selected_unit": next_id,
             "mission_count": int(state.mission_count), "dock_id": str(state.dock_id),
             "certified": bool(state.certified), "route_revalidation_required": bool(state.route_revalidation_required)},
        )


handle = unreal.register_slate_post_tick_callback(tick)
