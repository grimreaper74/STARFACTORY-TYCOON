"""Create the seated/standing control-room gameplay successor."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_MainControlRoom_OperatorEyeHeightCandidate_v035"
MAP = "/Game/LineBoss/Maps/LB_MainControlRoom_SeatedStandingCandidate_v036"
OUT = ROOT / "Saved/Audits/ControlRoom/main_control_room_seated_standing_build_v036.json"
CAPSULE_CENTRE_Z_CM = 88.0

library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if library.does_asset_exist(MAP):
    raise RuntimeError(f"refusing to overwrite {MAP}")
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"could not derive {MAP} from {BASE}")

failures = []
starts = [actor for actor in actors_api.get_all_level_actors() if isinstance(actor, unreal.PlayerStart)]
if len(starts) != 1:
    failures.append(f"expected exactly one PlayerStart, found {len(starts)}")
else:
    start = starts[0]
    old_location = start.get_actor_location()
    start.set_actor_location(unreal.Vector(old_location.x, old_location.y, CAPSULE_CENTRE_Z_CM), False, False)
    start.set_actor_label("LB_MCR_V036_PlayerStart_SeatedStanding")
    start.tags = [unreal.Name("LB.ControlRoom.v036"), unreal.Name("LB.ControlRoom.SeatedStandingOperator"),
                  unreal.Name("LB.Asset.CandidateNotPromoted")]

if failures:
    raise RuntimeError("; ".join(failures))

levels.save_current_level()
payload = {
    "$schema": "cairnwell/audit/main-control-room-seated-standing-build-v036/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__SEATED_STANDING_MAP_BUILT__COMPILE_RUNTIME_COLLISION_VISUAL_GATES_REQUIRED__NOT_PROMOTED",
    "source_map": BASE,
    "map": MAP,
    "capsule_centre_z_cm": CAPSULE_CENTRE_Z_CM,
    "seated_eye_height_cm": 130.0,
    "standing_eye_height_cm": 168.0,
    "stand_sit_input": "V",
    "standing_movement_input": "WASD",
    "chair_return_required_to_sit": True,
    "real_pr004_cctv_preserved": True,
    "corrected_monitor_orientation_preserved": True,
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({"status": payload["status"], "map": MAP, "audit": str(OUT)}, indent=2))
