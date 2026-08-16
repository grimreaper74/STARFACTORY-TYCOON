"""Move v025's persistent live feed onto the actual +Y CAMERA OVERVIEW wall."""

import json
import math
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = "/Game/LineBoss/Maps/LB_MainControlRoom_PR004LiveCCTVCandidate_v025"
MAP = "/Game/LineBoss/Maps/LB_MainControlRoom_PR004LiveCCTVWallCandidate_v027"
OUT = ROOT / "Saved/Audits/ControlRoom/main_control_room_pr004_live_cctv_wall_build_v027.json"
library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if library.does_asset_exist(MAP):
    raise RuntimeError(f"refusing to overwrite {MAP}")
if not levels.new_level_from_template(MAP, SOURCE):
    raise RuntimeError(f"could not derive {MAP}")

failures = []
feed = next((a for a in actors_api.get_all_level_actors()
             if a.get_class().get_name() == "LBControlRoomCCTVFeed"), None)
player_start = next((a for a in actors_api.get_all_level_actors() if isinstance(a, unreal.PlayerStart)), None)
seat = unreal.Vector(0.0, 82.0, 112.0)
target = unreal.Vector(68.0, 312.5, 170.0)
if feed is None:
    failures.append("persistent CCTV feed actor missing")
else:
    feed.set_actor_location(target, False, False)
    feed.set_actor_rotation(unreal.Rotator(pitch=0.0, yaw=180.0, roll=0.0), False)
    feed.set_actor_label("LB_MCR_V027_SELECTED_CCTV_PR004_WALL")
    feed.tags = [unreal.Name("LB.ControlRoom.v027"), unreal.Name("LB.CCTV.Selected.PR004"),
                 unreal.Name("LB.CCTV.Panel.CameraOverview"), unreal.Name("LB.Asset.CandidateNotPromoted")]
if player_start is None:
    failures.append("seated PlayerStart missing")
else:
    direction = target - seat
    horizontal = math.sqrt(direction.x * direction.x + direction.y * direction.y)
    player_start.set_actor_location(seat, False, False)
    player_start.set_actor_rotation(unreal.Rotator(
        pitch=math.degrees(math.atan2(direction.z, horizontal)),
        yaw=math.degrees(math.atan2(direction.y, direction.x)),
        roll=0.0), False)
    player_start.set_actor_label("LB_MCR_V027_PlayerStart_SelectedCCTVWall")
levels.save_current_level()

payload = {
    "$schema": "cairnwell/audit/main-control-room-pr004-live-cctv-wall-build-v027/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__LIVE_CCTV_MOVED_TO_ACTUAL_CAMERA_OVERVIEW_WALL__FRESH_RUNTIME_VISUAL_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__CONTROL_ROOM_CCTV_WALL_BUILD__NOT_PROMOTED",
    "source_map": SOURCE,
    "map": MAP,
    "display_location_cm": [target.x, target.y, target.z],
    "display_facing": "-Y toward seated operator",
    "seated_eye_cm": [seat.x, seat.y, seat.z],
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
