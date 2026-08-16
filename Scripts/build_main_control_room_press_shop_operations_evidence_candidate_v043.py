"""Freeze editor-visible native operations text in a preserved v042 successor."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_MainControlRoom_PressShopOperationsCandidate_v042"
MAP = "/Game/LineBoss/Maps/LB_MainControlRoom_PressShopOperationsEvidenceCandidate_v043"
OUT = ROOT / "Saved/Audits/ControlRoom/main_control_room_press_shop_operations_evidence_build_v043.json"
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
    operations[0].refresh_for_editor_evidence()
    operations[0].set_actor_label("LB_MCR_V043_PRESS_SHOP_OPERATIONS_CONSOLE")
    operations[0].tags = [
        unreal.Name("LB.ControlRoom.v043"), unreal.Name("LB.ControlRoom.PressShopOperations"),
        unreal.Name("LB.Authority.PlanningOnly"), unreal.Name("LB.Asset.CandidateNotPromoted")]

for camera in [a for a in actors_api.get_all_level_actors()
               if a.get_actor_label().startswith("LB_MCR_V042_CAM_")]:
    camera.set_actor_label(camera.get_actor_label().replace("V042", "V043"))
    camera.tags = [unreal.Name("LB.ControlRoom.v043"),
                   unreal.Name("LB.ControlRoom.Camera.OperationsEvidence"),
                   unreal.Name("LB.Asset.CandidateNotPromoted")]

levels.save_current_level()
payload = {
    "$schema": "cairnwell/audit/main-control-room-press-shop-operations-evidence-build-v043/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__EDITOR_VISIBLE_NATIVE_OPERATIONS_STATE_FROZEN__RUNTIME_VISUAL_GATE_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__CONTROL_ROOM_OPERATIONS_EVIDENCE_BUILD__NOT_PROMOTED",
    "source_map": BASE,
    "map": MAP,
    "authority_mutation": False,
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
if failures:
    raise RuntimeError("; ".join(failures))
print(json.dumps({"status": payload["status"], "map": MAP, "audit": str(OUT)}, indent=2))

