"""Exact v226 PIE gate for controller centre-view interaction from the authored player spawn."""

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import unreal


unreal.EditorPythonScripting.set_keep_python_script_alive(True)
ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v226"
OUT = ROOT / "Saved/Audits/ControlRoom/control_room_gamepad_interaction_pie_v226.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
unreal.EditorLevelLibrary.editor_play_simulate()

started = time.monotonic()
handle = None
respawn_requested_at = None


def finish(failures, evidence):
    global handle
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    payload = {
        "$schema": "cairnwell/audit/control-room-gamepad-interaction-pie-v226/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS__AUTHORED_PLAYERSTART_CENTRE_VIEW_REACHES_PHYSICAL_START_CONTROL__NOT_PROMOTED" if not failures else "FAIL__GAMEPAD_CENTRE_VIEW_INTERACTION__NOT_PROMOTED",
        "map": MAP,
        "evidence": evidence,
        "failures": failures,
        "promotion_authorized": False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    unreal.log(f"LB_V226_GAMEPAD_INTERACTION_{'PASS' if not failures else 'FAIL'}::{json.dumps(payload)}")
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()


def tick(_delta):
    global respawn_requested_at
    try:
        elapsed = time.monotonic() - started
        if elapsed > 35.0:
            finish(["timeout waiting for PIE world"], {})
            return
        if elapsed < 4.0:
            return
        world = unreal.EditorLevelLibrary.get_game_world()
        if world is None:
            return
        pawn = unreal.GameplayStatics.get_player_pawn(world, 0)
        controller = unreal.GameplayStatics.get_player_controller(world, 0)
        consoles = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBControlRoomOperationsConsole)
        if pawn is None or controller is None or len(consoles) != 1:
            finish([f"runtime objects missing: pawn={pawn is not None}, controller={controller is not None}, consoles={len(consoles)}"], {})
            return
        if not isinstance(pawn, unreal.LBControlRoomPawn):
            if isinstance(pawn, unreal.SpectatorPawn) and respawn_requested_at is None:
                starts = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.PlayerStart)
                game_mode = unreal.GameplayStatics.get_game_mode(world)
                if game_mode is None or len(starts) != 1:
                    finish([f"cannot replace simulate spectator: game_mode={game_mode is not None}, starts={len(starts)}"], {})
                    return
                game_mode.restart_player_at_player_start(controller, starts[0])
                respawn_requested_at = time.monotonic()
                return
            if respawn_requested_at is not None and time.monotonic() - respawn_requested_at < 3.0:
                return
            finish([f"unexpected pawn class after authored restart {pawn.get_class().get_name()}"], {})
            return
        console = consoles[0]
        cameras = pawn.get_components_by_class(unreal.CameraComponent)
        buttons = [component for component in console.get_components_by_class(unreal.BoxComponent)
                   if component.get_name() == "BTN_START"]
        if len(cameras) != 1 or len(buttons) != 1:
            finish([f"camera/button components missing: cameras={len(cameras)}, start_buttons={len(buttons)}"], {})
            return
        camera = cameras[0]
        button = buttons[0]
        camera_location = camera.get_world_location()
        button_location = button.get_world_location()
        distance_cm = (button_location - camera_location).length()
        look_at = unreal.MathLibrary.find_look_at_rotation(camera_location, button_location)
        controller.set_control_rotation(look_at)
        pawn.interact_at_view_centre()
        state = console.capture_save_state()
        evidence = {
            "pawn_class": pawn.get_class().get_name(),
            "camera_location_cm": str(camera_location),
            "start_button_location_cm": str(button_location),
            "interaction_distance_cm": distance_cm,
            "configured_trace_limit_cm": 900.0,
            "alarm_after_controller_interaction": state.last_alarm,
        }
        failures = []
        if distance_cm > 900.0:
            failures.append(f"authored Start button is beyond interaction range: {distance_cm:.2f} cm")
        if "START HELD" not in state.last_alarm:
            failures.append(f"centre-view interaction did not reach Start button: {state.last_alarm}")
        finish(failures, evidence)
    except Exception as exc:
        finish([f"validator exception: {type(exc).__name__}: {exc}"], {})


handle = unreal.register_slate_post_tick_callback(tick)
