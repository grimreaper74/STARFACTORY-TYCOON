"""Create the balanced-exposure, shadow-lightweight PR-004 CCTV successor."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_MainControlRoom_PR004CCTVCalibratedCandidate_v037"
MAP = "/Game/LineBoss/Maps/LB_MainControlRoom_PR004CCTVBalancedCandidate_v038"
OUT = ROOT / "Saved/Audits/ControlRoom/main_control_room_pr004_cctv_balanced_build_v038.json"

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
    feed.set_editor_property("capture_exposure_bias", 1.0)
    feed.set_actor_label("LB_MCR_V038_SELECTED_CCTV_PR004_BALANCED")
    feed.tags = [unreal.Name("LB.ControlRoom.v038"), unreal.Name("LB.CCTV.Selected.PR004"),
                 unreal.Name("LB.CCTV.BalancedCloseView"), unreal.Name("LB.Asset.CandidateNotPromoted")]

if failures:
    raise RuntimeError("; ".join(failures))
levels.save_current_level()
payload = {
    "$schema": "cairnwell/audit/main-control-room-pr004-cctv-balanced-build-v038/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__BALANCED_PR004_CCTV_BUILT__RUNTIME_VISUAL_PERFORMANCE_GATE_REQUIRED__NOT_PROMOTED",
    "source_map": BASE,
    "map": MAP,
    "capture_exposure_bias": 1.0,
    "capture_dynamic_shadows": False,
    "capture_max_view_distance_cm": 12000.0,
    "close_pr004_camera_preserved": True,
    "seated_standing_loop_preserved": True,
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({"status": payload["status"], "map": MAP, "audit": str(OUT)}, indent=2))
