"""Read-only bounds inspection for v085 PR-009 guard, HMI and cell actors."""
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR009LayeredPresentationCandidate_v085"
OUT = ROOT / "Saved/Audits/press_shop_pr009_presentation_bounds_v085.json"
WANTED = ("GuardSet", "HMI_01", "ElectricalCabinet", "TracePortal", "Carrier_01", "VisionCentre")

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

records = []
for actor in actors_api.get_all_level_actors():
    label = actor.get_actor_label()
    if not any(token in label for token in WANTED):
        continue
    origin, extent = actor.get_actor_bounds(False, True)
    records.append({
        "actor": label,
        "origin_cm": [origin.x, origin.y, origin.z],
        "extent_cm": [extent.x, extent.y, extent.z],
        "min_cm": [origin.x - extent.x, origin.y - extent.y, origin.z - extent.z],
        "max_cm": [origin.x + extent.x, origin.y + extent.y, origin.z + extent.z],
    })

payload = {
    "$schema": "cairnwell/audit/press-shop-pr009-presentation-bounds-v085/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PR009_V085_READ_ONLY_PRESENTATION_BOUNDS_COMPLETE",
    "map": MAP,
    "records": records,
    "map_modified": False,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
unreal.log(payload["status"])
unreal.SystemLibrary.quit_editor()
