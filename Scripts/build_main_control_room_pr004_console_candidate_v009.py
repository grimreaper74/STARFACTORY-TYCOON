"""Mount the real authority-backed PR-004 HMI on the corrected playable bank."""

import json
import math
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_MainControlRoom_OperatorAimCandidate_v008"
MAP = "/Game/LineBoss/Maps/LB_MainControlRoom_PR004ConsoleCandidate_v009"
OUT = ROOT / "Saved/Audits/ControlRoom/main_control_room_pr004_console_build_v009.json"

library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
failures = []

if library.does_asset_exist(MAP):
    raise RuntimeError(f"refusing to overwrite {MAP}")
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"could not derive {MAP}")

console_class = unreal.load_class(None, "/Script/LineBossCarFactory.LBControlRoomPR004Console")
if console_class is None:
    failures.append("could not load LBControlRoomPR004Console class")
else:
    # Pro/source PLANT_OVERVIEW panel datum: (-1840, +977.8, 1490) mm.
    # Blender +Y converts to Unreal -Y. Offset the live plane 3 cm toward the
    # seated player to prevent z-fighting with the replaceable authored UI.
    screen = unreal.Vector(-184.0, -97.78, 149.0)
    seat = unreal.Vector(0.0, 82.0, 112.0)
    direction = seat - screen
    horizontal = math.sqrt(direction.x * direction.x + direction.y * direction.y)
    yaw = math.degrees(math.atan2(direction.y, direction.x))
    pitch = math.degrees(math.atan2(direction.z, horizontal))
    length = math.sqrt(direction.x * direction.x + direction.y * direction.y + direction.z * direction.z)
    offset = direction * (3.0 / length)
    location = screen + offset
    rotation = unreal.Rotator(pitch, yaw, 0.0)
    console = actors_api.spawn_actor_from_class(console_class, location, rotation)
    if console is None:
        failures.append("could not spawn authority-backed PR-004 console")
    else:
        console.set_actor_label("LB_MCR_V009_PR004_AuthorityConsole")
        console.set_actor_scale3d(unreal.Vector(0.90, 0.90, 0.90))
        console.tags = [
            unreal.Name("LB.ControlRoom.v009"),
            unreal.Name("LB.ControlRoom.Console.PR004"),
            unreal.Name("LB.Authority.PR004.Live"),
            unreal.Name("LB.Asset.CandidateNotPromoted"),
        ]

for actor in actors_api.get_all_level_actors():
    if any(str(tag) == "LB.ControlRoom.v008" for tag in actor.tags):
        actor.tags = [unreal.Name("LB.ControlRoom.v009" if str(tag) == "LB.ControlRoom.v008" else str(tag)) for tag in actor.tags]

levels.save_current_level()
payload = {
    "$schema": "cairnwell/audit/main-control-room-pr004-console-build-v009/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__REAL_PR004_AUTHORITY_HMI_MOUNTED__RUNTIME_AND_POINTER_GATE_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__PR004_CONTROL_ROOM_CONSOLE_BUILD__NOT_PROMOTED",
    "source_map": BASE,
    "map": MAP,
    "console_class": "/Script/LineBossCarFactory.LBControlRoomPR004Console",
    "widget_class": "/Script/LineBossCarFactory.LBPR004HMIWidget",
    "authority_class": "/Script/LineBossCarFactory.LBPR004Station",
    "mount_role": "PLANT_OVERVIEW panel used as selected PR-004 station detail view",
    "source_screen_datum_cm": [-184.0, -97.78, 149.0],
    "seated_eye_cm": [0.0, 82.0, 112.0],
    "mounted_location_cm": [round(location.x, 3), round(location.y, 3), round(location.z, 3)] if console_class else None,
    "mounted_rotation_deg": [round(pitch, 3), round(yaw, 3), 0.0] if console_class else None,
    "widget_world_dimensions_cm": [64.8, 36.45],
    "bootstrap_state": "packaged coil loaded / recipe selected / cradle locked / C-hook withdrawn / player action ready",
    "fake_state_used": False,
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({"status": payload["status"], "failures": failures, "audit": str(OUT)}, indent=2))
