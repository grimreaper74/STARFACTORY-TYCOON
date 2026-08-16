"""Correct the v043 terminal's scripted Rotator axis assignment without moving its datum."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_MainControlRoom_PressShopOperationsEvidenceCandidate_v043"
MAP = "/Game/LineBoss/Maps/LB_MainControlRoom_PressShopOperationsRotationCandidate_v044"
OUT = ROOT / "Saved/Audits/ControlRoom/main_control_room_press_shop_operations_rotation_build_v044.json"
library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if library.does_asset_exist(MAP):
    raise RuntimeError(f"refusing to overwrite {MAP}")
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"could not derive {MAP} from {BASE}")

failures = []
operations = [a for a in actors_api.get_all_level_actors()
              if a.get_class().get_name() == "LBControlRoomOperationsConsole"]
if len(operations) != 1:
    failures.append(f"expected one operations console, found {len(operations)}")
else:
    console = operations[0]
    rotation = unreal.Rotator()
    rotation.pitch = -12.0
    rotation.yaw = 98.786
    rotation.roll = 0.0
    console.set_actor_rotation(rotation, False)
    console.refresh_for_editor_evidence()
    console.set_actor_label("LB_MCR_V044_PRESS_SHOP_OPERATIONS_CONSOLE")
    console.tags = [unreal.Name("LB.ControlRoom.v044"),
                    unreal.Name("LB.ControlRoom.PressShopOperations"),
                    unreal.Name("LB.Authority.PlanningOnly"),
                    unreal.Name("LB.Asset.CandidateNotPromoted")]

for camera in [a for a in actors_api.get_all_level_actors()
               if a.get_actor_label().startswith("LB_MCR_V043_CAM_")]:
    camera.set_actor_label(camera.get_actor_label().replace("V043", "V044"))
    camera.tags = [unreal.Name("LB.ControlRoom.v044"),
                   unreal.Name("LB.ControlRoom.Camera.OperationsEvidence"),
                   unreal.Name("LB.Asset.CandidateNotPromoted")]

levels.save_current_level()
payload = {
    "$schema": "cairnwell/audit/main-control-room-press-shop-operations-rotation-build-v044/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__EXACT_ROTATOR_AXES_CORRECTED__FRESH_VISUAL_GATE_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__CONTROL_ROOM_OPERATIONS_ROTATION_BUILD__NOT_PROMOTED",
    "source_map": BASE,
    "map": MAP,
    "rejected_predecessor": {
        "map": BASE,
        "decision": "REJECTED_PRESENTATION__ROTATOR_AXES_MISASSIGNED__SCREEN_NEAR_HORIZONTAL",
    },
    "corrected_rotation_deg": {"pitch": -12.0, "yaw": 98.786, "roll": 0.0},
    "authority_mutation": False,
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
if failures: raise RuntimeError("; ".join(failures))
print(json.dumps({"status": payload["status"], "map": MAP, "audit": str(OUT)}, indent=2))

