"""Raise the fixed seated operator eye point after v034 monitor correction."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_MainControlRoom_MonitorVerticalCandidate_v034"
MAP = "/Game/LineBoss/Maps/LB_MainControlRoom_OperatorEyeHeightCandidate_v035"
OUT = ROOT / "Saved/Audits/ControlRoom/main_control_room_operator_eye_height_build_v035.json"
EYE_HEIGHT_CM = 130.0

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
    start.set_actor_location(unreal.Vector(old_location.x, old_location.y, EYE_HEIGHT_CM), False, False)
    start.set_actor_label("LB_MCR_V035_PlayerStart_RaisedSeatedEye")
    start.tags = [unreal.Name("LB.ControlRoom.v035"), unreal.Name("LB.ControlRoom.FixedSeatedOperator"),
                  unreal.Name("LB.Asset.CandidateNotPromoted")]

if failures:
    raise RuntimeError("; ".join(failures))

levels.save_current_level()
payload = {
    "$schema": "cairnwell/audit/main-control-room-operator-eye-height-build-v035/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__RAISED_SEATED_EYE_POINT_BUILT__RUNTIME_VISUAL_GATE_REQUIRED__NOT_PROMOTED",
    "source_map": BASE,
    "map": MAP,
    "old_eye_height_cm": old_location.z,
    "new_eye_height_cm": EYE_HEIGHT_CM,
    "translation_remains_disabled": True,
    "monitor_source_rotation_from_horizontal_degrees": 78.0,
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({"status": payload["status"], "map": MAP, "audit": str(OUT)}, indent=2))
