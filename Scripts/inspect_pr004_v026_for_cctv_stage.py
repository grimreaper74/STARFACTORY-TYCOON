"""Read-only actor/camera/light inventory for the retained PR-004 v026 map."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004PackagingPolishCandidate_v026"
OUT = ROOT / "Saved/Audits/ControlRoom/pr004_v026_cctv_stage_source_inspection.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"could not load {MAP}")

records = []
for actor in actors_api.get_all_level_actors():
    class_name = actor.get_class().get_name()
    if any(token in class_name for token in ("Camera", "Light", "Sky", "PR004", "PostProcess")):
        loc = actor.get_actor_location()
        rot = actor.get_actor_rotation()
        records.append({
            "label": actor.get_actor_label(),
            "class": class_name,
            "location_cm": [round(loc.x, 3), round(loc.y, 3), round(loc.z, 3)],
            "rotation_deg": [round(rot.pitch, 3), round(rot.yaw, 3), round(rot.roll, 3)],
            "hidden": actor.is_hidden_ed(),
            "tags": [str(tag) for tag in actor.tags],
        })

payload = {
    "$schema": "cairnwell/audit/pr004-v026-cctv-stage-source-inspection/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "READ_ONLY_SOURCE_INSPECTION",
    "map": MAP,
    "matching_actor_count": len(records),
    "actors": records,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({"status": payload["status"], "count": len(records), "audit": str(OUT)}, indent=2))
