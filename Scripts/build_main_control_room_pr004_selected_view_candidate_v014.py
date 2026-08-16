"""Derive v014 with the seated pawn initially looking at the live PR-004 HMI."""

import json
import math
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_MainControlRoom_PR004ConsoleCandidate_v013"
MAP = "/Game/LineBoss/Maps/LB_MainControlRoom_PR004SelectedViewCandidate_v014"
OUT = ROOT / "Saved/Audits/ControlRoom/main_control_room_pr004_selected_view_build_v014.json"
library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if library.does_asset_exist(MAP):
    raise RuntimeError(f"refusing to overwrite {MAP}")
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"could not derive {MAP}")

failures = []
seat = unreal.Vector(0.0, 82.0, 112.0)
target = unreal.Vector(-183.545, -94.884, 148.376)
direction = target - seat
horizontal = math.sqrt(direction.x * direction.x + direction.y * direction.y)
yaw = math.degrees(math.atan2(direction.y, direction.x))
pitch = math.degrees(math.atan2(direction.z, horizontal))
player_start = next((a for a in actors_api.get_all_level_actors() if isinstance(a, unreal.PlayerStart)), None)
if player_start is None:
    failures.append("missing inherited seated PlayerStart")
else:
    player_start.set_actor_location(seat, False, False)
    player_start.set_actor_rotation(unreal.Rotator(pitch=pitch, yaw=yaw, roll=0.0), False)
    player_start.set_actor_label("LB_MCR_V014_PlayerStart_PR004Selected")
    player_start.tags = [
        unreal.Name("LB.ControlRoom.v014"),
        unreal.Name("LB.ControlRoom.PlayerStart.Seated"),
        unreal.Name("LB.ControlRoom.InitialView.PR004"),
        unreal.Name("LB.Asset.CandidateNotPromoted"),
    ]

for actor in actors_api.get_all_level_actors():
    if any(str(tag) == "LB.ControlRoom.v013" for tag in actor.tags):
        actor.tags = [unreal.Name("LB.ControlRoom.v014" if str(tag) == "LB.ControlRoom.v013" else str(tag)) for tag in actor.tags]
levels.save_current_level()
payload = {
    "$schema": "cairnwell/audit/main-control-room-pr004-selected-view-build-v014/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__SEATED_INITIAL_VIEW_AIMS_AT_LIVE_PR004_HMI__RUNTIME_VISUAL_GATE_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__PR004_SELECTED_VIEW_BUILD__NOT_PROMOTED",
    "source_map": BASE,
    "map": MAP,
    "seated_eye_cm": [seat.x, seat.y, seat.z],
    "selected_hmi_target_cm": [target.x, target.y, target.z],
    "initial_control_rotation_deg": [round(pitch, 3), round(yaw, 3), 0.0],
    "player_translation_enabled": False,
    "player_look_enabled": True,
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({"status": payload["status"], "failures": failures, "audit": str(OUT)}, indent=2))
