"""Retain v036 gameplay and calibrate the real PR-004 selected CCTV feed."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_MainControlRoom_SeatedStandingCandidate_v036"
MAP = "/Game/LineBoss/Maps/LB_MainControlRoom_PR004CCTVCalibratedCandidate_v037"
OUT = ROOT / "Saved/Audits/ControlRoom/main_control_room_pr004_cctv_calibrated_build_v037.json"
STAGE_OFFSET = unreal.Vector(200000.0, 0.0, 0.0)
SOURCE_LOCATION = unreal.Vector(-5850.0, -330.0, 720.0)
SOURCE_ROTATION = unreal.Rotator(pitch=-17.953, yaw=-64.404, roll=0.0)

library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if library.does_asset_exist(MAP):
    raise RuntimeError(f"refusing to overwrite {MAP}")
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"could not derive {MAP} from {BASE}")

failures = []
feeds = [actor for actor in actors_api.get_all_level_actors()
         if actor.get_class().get_name() == "LBControlRoomCCTVFeed"]
if len(feeds) != 1:
    failures.append(f"expected exactly one CCTV feed, found {len(feeds)}")
else:
    feed = feeds[0]
    feed.set_editor_property("capture_world_location", SOURCE_LOCATION + STAGE_OFFSET)
    feed.set_editor_property("capture_world_rotation", SOURCE_ROTATION)
    feed.set_editor_property("capture_exposure_bias", -1.0)
    feed.set_editor_property("selected_feed", True)
    feed.set_actor_label("LB_MCR_V037_SELECTED_CCTV_PR004_CALIBRATED")
    feed.tags = [unreal.Name("LB.ControlRoom.v037"), unreal.Name("LB.CCTV.Selected.PR004"),
                 unreal.Name("LB.CCTV.CalibratedCloseView"), unreal.Name("LB.Asset.CandidateNotPromoted")]

if failures:
    raise RuntimeError("; ".join(failures))

levels.save_current_level()
payload = {
    "$schema": "cairnwell/audit/main-control-room-pr004-cctv-calibrated-build-v037/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__CALIBRATED_REAL_PR004_CCTV_BUILT__RUNTIME_VISUAL_PERFORMANCE_GATE_REQUIRED__NOT_PROMOTED",
    "source_map": BASE,
    "map": MAP,
    "source_camera": "LB_INT_PR004_V009_CAM_PR004CloseDirty",
    "capture_source_location_cm": [SOURCE_LOCATION.x, SOURCE_LOCATION.y, SOURCE_LOCATION.z],
    "capture_source_rotation_deg": [SOURCE_ROTATION.pitch, SOURCE_ROTATION.yaw, SOURCE_ROTATION.roll],
    "stage_offset_cm": [STAGE_OFFSET.x, STAGE_OFFSET.y, STAGE_OFFSET.z],
    "capture_exposure_bias": -1.0,
    "capture_max_view_distance_cm": 12000.0,
    "seated_standing_loop_preserved": True,
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({"status": payload["status"], "map": MAP, "audit": str(OUT)}, indent=2))
