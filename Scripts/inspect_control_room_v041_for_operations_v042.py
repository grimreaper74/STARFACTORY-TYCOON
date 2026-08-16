"""Read-only placement audit for the v042 Press Shop operations terminal."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_MainControlRoom_PR004CCTVDormantCandidate_v041"
OUT = ROOT / "Saved/Audits/ControlRoom/main_control_room_operations_placement_inspection_v041.json"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"could not load {MAP}")

records = []
for actor in actors_api.get_all_level_actors():
    transform = actor.get_actor_transform()
    location = transform.translation
    rotation = transform.rotation.rotator()
    records.append({
        "label": actor.get_actor_label(),
        "class": actor.get_class().get_name(),
        "location_cm": [location.x, location.y, location.z],
        "rotation_deg": [rotation.pitch, rotation.yaw, rotation.roll],
        "tags": [str(tag) for tag in actor.tags],
    })

payload = {
    "$schema": "cairnwell/audit/control-room-operations-placement-v041/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "READ_ONLY_INSPECTION",
    "map": MAP,
    "actors": sorted(records, key=lambda item: item["label"]),
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({"status": payload["status"], "actor_count": len(records), "audit": str(OUT)}, indent=2))
