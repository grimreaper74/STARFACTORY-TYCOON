"""Derive v007 from the monitor-corrected v006 map and enable seated play."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_MainControlRoom_MonitorPitchCandidate_v006"
MAP = "/Game/LineBoss/Maps/LB_MainControlRoom_PlayableCandidate_v007"
OUT = ROOT / "Saved/Audits/ControlRoom/main_control_room_playable_build_v007.json"

library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if library.does_asset_exist(MAP):
    raise RuntimeError(f"refusing to overwrite {MAP}")
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"could not derive {MAP}")

failures = []
game_mode_class = unreal.load_class(None, "/Script/LineBossCarFactory.LBControlRoomGameMode")
if game_mode_class is None:
    failures.append("could not load LBControlRoomGameMode class")
else:
    world = unreal.EditorLevelLibrary.get_editor_world()
    world_settings = world.get_world_settings()
    world_settings.set_editor_property("default_game_mode", game_mode_class)

camera = next((actor for actor in actors_api.get_all_level_actors() if actor.get_actor_label() == "LB_MCR_V006_CAM_SeatedPlayer"), None)
if camera is None:
    failures.append("missing v006 seated evidence camera")
    seat_location = unreal.Vector(0, 82, 112)
    seat_rotation = unreal.Rotator(10.6, -90.0, 0.0)
else:
    seat_location = camera.get_actor_location()
    seat_rotation = camera.get_actor_rotation()

player_start = actors_api.spawn_actor_from_class(unreal.PlayerStart, seat_location, seat_rotation)
if player_start is None:
    failures.append("could not spawn seated PlayerStart")
else:
    player_start.set_actor_label("LB_MCR_V007_PlayerStart_Seated1120")
    player_start.tags = [
        unreal.Name("LB.ControlRoom.v007"),
        unreal.Name("LB.ControlRoom.PlayerStart.Seated"),
        unreal.Name("LB.Asset.CandidateNotPromoted"),
    ]

for actor in actors_api.get_all_level_actors():
    if any(str(tag) == "LB.ControlRoom.v006" for tag in actor.tags):
        actor.tags = [unreal.Name("LB.ControlRoom.v007" if str(tag) == "LB.ControlRoom.v006" else str(tag)) for tag in actor.tags]

levels.save_current_level()
payload = {
    "$schema": "cairnwell/audit/main-control-room-playable-build-v007/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__SEATED_CONTROL_ROOM_PAWN_AND_GAME_MODE_ASSIGNED__RUNTIME_GATE_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__CONTROL_ROOM_V007_PLAYABLE_BUILD__NOT_PROMOTED",
    "source_map": BASE,
    "map": MAP,
    "game_mode": "/Script/LineBossCarFactory.LBControlRoomGameMode",
    "default_pawn": "/Script/LineBossCarFactory.LBControlRoomPawn",
    "seated_eye_location_cm": [round(seat_location.x, 3), round(seat_location.y, 3), round(seat_location.z, 3)],
    "translation_enabled": False,
    "interaction_enabled": True,
    "live_factory_feed_wired": False,
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({"status": payload["status"], "failures": failures, "audit": str(OUT)}, indent=2))

