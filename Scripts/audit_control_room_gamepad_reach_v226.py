"""Static exact-map range audit for the controller centre-view interaction path."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v226"
OUT = ROOT / "Saved/Audits/ControlRoom/control_room_gamepad_authored_reach_v226.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
starts = [actor for actor in actors if isinstance(actor, unreal.PlayerStart)]
consoles = [actor for actor in actors if isinstance(actor, unreal.LBControlRoomOperationsConsole)]
failures = []
evidence = {}
if len(starts) != 1 or len(consoles) != 1:
    failures.append(f"expected one PlayerStart and console, found {len(starts)} and {len(consoles)}")
else:
    start = starts[0]
    console = consoles[0]
    buttons = [component for component in console.get_components_by_class(unreal.BoxComponent)
               if component.get_name() == "BTN_START"]
    if len(buttons) != 1:
        failures.append(f"expected one BTN_START, found {len(buttons)}")
    else:
        eye = start.get_actor_location() + unreal.Vector(0.0, 0.0, 80.0)
        target = buttons[0].get_world_location()
        distance_cm = (target - eye).length()
        evidence = {
            "player_start_location_cm": str(start.get_actor_location()),
            "standing_eye_location_cm": str(eye),
            "start_button_location_cm": str(target),
            "straight_line_distance_cm": distance_cm,
            "configured_trace_limit_cm": 900.0,
        }
        if distance_cm > 900.0:
            failures.append(f"Start button is beyond interaction limit: {distance_cm:.2f} cm")
payload = {
    "$schema": "cairnwell/audit/control-room-gamepad-authored-reach-v226/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__AUTHORED_PLAYERSTART_WITHIN_CONTROLLER_INTERACTION_RANGE__NOT_PROMOTED" if not failures else "FAIL__AUTHORED_CONTROLLER_INTERACTION_RANGE__NOT_PROMOTED",
    "map": MAP,
    "evidence": evidence,
    "failures": failures,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LB_V226_GAMEPAD_REACH_{'PASS' if not failures else 'FAIL'}::{json.dumps(payload)}")
unreal.SystemLibrary.quit_editor()
