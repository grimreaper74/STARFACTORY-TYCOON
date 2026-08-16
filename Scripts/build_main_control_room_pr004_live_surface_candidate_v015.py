"""Derive v015 with the live HMI in front of authored placeholder UI layers."""

import json
import math
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_MainControlRoom_PR004SelectedViewCandidate_v014"
MAP = "/Game/LineBoss/Maps/LB_MainControlRoom_PR004LiveSurfaceCandidate_v015"
OUT = ROOT / "Saved/Audits/ControlRoom/main_control_room_pr004_live_surface_build_v015.json"
library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if library.does_asset_exist(MAP):
    raise RuntimeError(f"refusing to overwrite {MAP}")
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"could not derive {MAP}")

failures = []
console = next((a for a in actors_api.get_all_level_actors() if isinstance(a, unreal.LBControlRoomPR004Console)), None)
yaw = 90.0 - 8.786
pitch = -12.0
pitch_rad = math.radians(pitch)
yaw_rad = math.radians(yaw)
normal = unreal.Vector(
    math.cos(pitch_rad) * math.cos(yaw_rad),
    math.cos(pitch_rad) * math.sin(yaw_rad),
    math.sin(pitch_rad),
)
screen = unreal.Vector(-184.0, -97.78, 149.0)
location = screen + normal * 8.0
if console is None:
    failures.append("missing inherited authority-backed PR-004 console")
else:
    console.set_actor_location(location, False, False)
    console.set_actor_rotation(unreal.Rotator(pitch=pitch, yaw=yaw, roll=0.0), False)
    console.set_actor_label("LB_MCR_V015_PR004_AuthorityConsole")
    console.tags = [
        unreal.Name("LB.ControlRoom.v015"),
        unreal.Name("LB.ControlRoom.Console.PR004"),
        unreal.Name("LB.Authority.PR004.Live"),
        unreal.Name("LB.Asset.CandidateNotPromoted"),
    ]

for actor in actors_api.get_all_level_actors():
    if any(str(tag) == "LB.ControlRoom.v014" for tag in actor.tags):
        actor.tags = [unreal.Name("LB.ControlRoom.v015" if str(tag) == "LB.ControlRoom.v014" else str(tag)) for tag in actor.tags]
levels.save_current_level()
payload = {
    "$schema": "cairnwell/audit/main-control-room-pr004-live-surface-build-v015/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__LIVE_PR004_HMI_IN_FRONT_OF_AUTHORED_PLACEHOLDER__RUNTIME_VISUAL_AND_POINTER_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__PR004_LIVE_SURFACE_BUILD__NOT_PROMOTED",
    "source_map": BASE,
    "map": MAP,
    "screen_centre_cm": [screen.x, screen.y, screen.z],
    "live_surface_offset_cm": 8.0,
    "authored_placeholder_offset_cm": 5.2,
    "live_surface_location_cm": [round(location.x, 3), round(location.y, 3), round(location.z, 3)],
    "live_surface_rotation_deg": [pitch, round(yaw, 3), 0.0],
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({"status": payload["status"], "failures": failures, "audit": str(OUT)}, indent=2))
