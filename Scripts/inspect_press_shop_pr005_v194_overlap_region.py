"""Read-only actor inventory inside the v194 candidate enclosure envelope."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR005ExteriorIntegrationCandidate_v194"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/PressShopIntegration/press_shop_pr005_v194_overlap_region.json"
MIN = unreal.Vector(-4550.0, -2350.0, -25.0)
MAX = unreal.Vector(-3450.0, -1650.0, 500.0)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)


def vector(value):
    return [round(float(component), 6) for component in value.to_tuple()]


rows = []
for actor in actors_api.get_all_level_actors():
    origin, extent = actor.get_actor_bounds(False)
    actor_min = origin - extent
    actor_max = origin + extent
    overlaps = not (
        actor_max.x < MIN.x or actor_min.x > MAX.x
        or actor_max.y < MIN.y or actor_min.y > MAX.y
        or actor_max.z < MIN.z or actor_min.z > MAX.z
    )
    if not overlaps:
        continue
    row = {
        "label": actor.get_actor_label(),
        "class": actor.get_class().get_path_name(),
        "location_cm": vector(actor.get_actor_location()),
        "bounds_min_cm": vector(actor_min),
        "bounds_max_cm": vector(actor_max),
        "tags": [str(tag) for tag in actor.tags],
    }
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    if component is not None:
        mesh = component.static_mesh
        row.update({
            "static_mesh": mesh.get_path_name() if mesh else None,
            "collision_enabled": str(component.get_collision_enabled()),
            "collision_profile": str(component.get_collision_profile_name()),
            "can_affect_navigation": bool(component.get_editor_property("can_ever_affect_navigation")),
        })
    rows.append(row)

rows.sort(key=lambda item: item["label"])
payload = {
    "$schema": "cairnwell/audit/press-shop-pr005-v194-overlap-region/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "READ_ONLY_OVERLAP_INVENTORY__NO_ACTORS_CHANGED",
    "map": MAP,
    "envelope_min_cm": vector(MIN),
    "envelope_max_cm": vector(MAX),
    "actor_count": len(rows),
    "actors": rows,
    "map_modified": False,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({"status": payload["status"], "actor_count": len(rows)}, indent=2))
