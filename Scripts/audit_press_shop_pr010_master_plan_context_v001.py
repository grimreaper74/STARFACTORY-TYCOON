"""Read-only accepted-map context audit around the fixed PR-010 datum."""

import json
import math
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR009Accepted_v095"
OUT = ROOT / "Saved/Audits/PR010_Intake/pr010_master_plan_context_v001.json"
OUT.parent.mkdir(parents=True, exist_ok=True)
DATUM = unreal.Vector(1350.0, -2000.0, 0.0)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)

rows = []
named = []
for actor in actors_api.get_all_level_actors():
    location = actor.get_actor_location()
    distance = math.sqrt((location.x-DATUM.x)**2 + (location.y-DATUM.y)**2 + (location.z-DATUM.z)**2)
    label = actor.get_actor_label()
    tags = [str(tag) for tag in actor.tags]
    row = {
        "label": label,
        "class": actor.get_class().get_name(),
        "location_cm": [location.x, location.y, location.z],
        "rotation_deg": [actor.get_actor_rotation().roll, actor.get_actor_rotation().pitch, actor.get_actor_rotation().yaw],
        "distance_to_pr010_datum_cm": distance,
        "tags": tags,
    }
    if "PR010" in label.upper() or any("PR010" in tag.upper() for tag in tags):
        named.append(row)
    if distance <= 2000.0:
        rows.append(row)

rows.sort(key=lambda row: row["distance_to_pr010_datum_cm"])
named.sort(key=lambda row: row["distance_to_pr010_datum_cm"])
result = {
    "$schema": "cairnwell/audit/pr010-master-plan-context-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "map": MAP,
    "fixed_datum_cm": [1350, -2000, 0],
    "named_pr010_actor_count": len(named),
    "named_pr010_actors": named,
    "nearest_actor_count_within_2000_cm": len(rows),
    "nearest_actors": rows[:600],
    "status": "CONTEXT_CAPTURED__ROTATION_REQUIRES_MEASURED_INTERPRETATION__NOT_PROMOTED",
    "promotion_authorized": False,
}
OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR010_CONTEXT {result['status']} named={len(named)} nearby={len(rows)} {OUT}")
