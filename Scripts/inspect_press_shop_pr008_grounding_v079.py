"""Read-only inventory of detailed PR-008 actors that reach the v079 floor/base zone."""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR008CalibratedLightingCandidate_v079"
AUDIT = ROOT / "Saved/Audits/press_shop_pr008_grounding_inventory_v079.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

eligible = re.compile(r"^LB_PR008_V063_|^LB_PR008_V06[4-9]_SM_|^LB_PR008_V07[0-3]_SM_")
rows = []
for actor in actors.get_all_level_actors():
    label = actor.get_actor_label()
    if not eligible.match(label):
        continue
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    if component is None or component.static_mesh is None:
        continue
    origin, extent = actor.get_actor_bounds(False, False)
    minimum = [origin.x - extent.x, origin.y - extent.y, origin.z - extent.z]
    maximum = [origin.x + extent.x, origin.y + extent.y, origin.z + extent.z]
    if minimum[2] > 20.0:
        continue
    rows.append({
        "actor": label,
        "mesh": component.static_mesh.get_path_name(),
        "origin_cm": [origin.x, origin.y, origin.z],
        "extent_cm": [extent.x, extent.y, extent.z],
        "minimum_cm": minimum,
        "maximum_cm": maximum,
        "footprint_cm": [extent.x * 2.0, extent.y * 2.0],
    })

rows.sort(key=lambda row: (row["origin_cm"][0], row["origin_cm"][1], row["actor"]))
payload = {
    "$schema": "line-boss/audit/press-shop-pr008-grounding-inventory-v079/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "READ_ONLY_PR008_DETAILED_BASE_FOOTPRINT_INVENTORY_COMPLETE__NO_ASSETS_MODIFIED",
    "map": MAP,
    "floor_reach_threshold_cm": 20.0,
    "actor_count": len(rows),
    "actors": rows,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR008_V079_GROUNDING_INVENTORY_PASS actors={len(rows)}")
