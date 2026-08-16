"""Rebuild the selected CCTV actor in v032 after adding pointer focus and throttling gates."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_MainControlRoom_PR004LiveCCTVAuthoredSeatCandidate_v032"
MAP = "/Game/LineBoss/Maps/LB_MainControlRoom_PR004CCTVFocusCandidate_v033"
OUT = ROOT / "Saved/Audits/ControlRoom/main_control_room_pr004_cctv_focus_build_v033.json"

library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
failures = []

if library.does_asset_exist(MAP):
    raise RuntimeError(f"refusing to overwrite {MAP}")
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"could not derive {MAP} from {BASE}")

feed_class = unreal.load_class(None, "/Script/LineBossCarFactory.LBControlRoomCCTVFeed")
old_feed = next((a for a in actors_api.get_all_level_actors()
                 if a.get_class().get_name() == "LBControlRoomCCTVFeed"), None)
if feed_class is None or old_feed is None:
    failures.append("compiled CCTV class or inherited v032 feed missing")
else:
    location = old_feed.get_actor_location()
    rotation = old_feed.get_actor_rotation()
    scale = old_feed.get_actor_scale3d()
    capture_location = old_feed.get_editor_property("capture_world_location")
    capture_rotation = old_feed.get_editor_property("capture_world_rotation")
    actors_api.destroy_actor(old_feed)
    feed = actors_api.spawn_actor_from_class(feed_class, location, rotation)
    if feed is None:
        failures.append("could not spawn fresh focus-enabled CCTV actor")
    else:
        feed.set_actor_scale3d(scale)
        feed.set_editor_property("capture_world_location", capture_location)
        feed.set_editor_property("capture_world_rotation", capture_rotation)
        feed.set_editor_property("selected_feed", True)
        feed.set_actor_label("LB_MCR_V033_SELECTED_CCTV_PR004_FOCUSABLE")
        feed.tags = [unreal.Name("LB.ControlRoom.v033"), unreal.Name("LB.CCTV.Selected.PR004"),
                     unreal.Name("LB.CCTV.PointerFocus"), unreal.Name("LB.Asset.CandidateNotPromoted")]

if not levels.save_current_level():
    failures.append("could not save v033 focus candidate")

payload = {
    "$schema": "cairnwell/audit/main-control-room-pr004-cctv-focus-build-v033/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__FRESH_POINTER_FOCUS_CCTV_ACTOR_BUILT__RUNTIME_VISUAL_GATE_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__CONTROL_ROOM_CCTV_FOCUS_BUILD__NOT_PROMOTED",
    "source_map": BASE,
    "map": MAP,
    "interaction": "visibility trace/click or C key focuses selected feed; Home restores authored view",
    "focused_fov_degrees": 38.0,
    "selected_capture": "1280x720 every frame",
    "inactive_capture": "every-frame and movement capture disabled; last frame retained",
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({"status": payload["status"], "failures": failures, "audit": str(OUT)}, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
