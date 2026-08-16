"""Read-only PR-005 v053 inventory for authority-safe enclosure alignment."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR005LogisticsCandidate_v053"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/PressShopIntegration/press_shop_pr005_v053_integration_datums.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)


def vec(value):
    return [round(float(v), 6) for v in value.to_tuple()]


rows = []
native_station = []
for actor in actors_api.get_all_level_actors():
    label = actor.get_actor_label()
    tags = [str(tag) for tag in actor.tags]
    class_path = actor.get_class().get_path_name()
    is_pr005 = (
        "PR005" in label.upper()
        or "PR-005" in label.upper()
        or any("PR005" in tag.upper() or "PR-005" in tag.upper() for tag in tags)
        or "LBPR005Station" in class_path
    )
    if not is_pr005:
        continue
    transform = actor.get_actor_transform()
    row = {
        "label": label,
        "class": class_path,
        "location_cm": vec(transform.translation),
        "rotation_deg": vec(transform.rotation.rotator()),
        "scale": vec(transform.scale3d),
        "tags": tags,
    }
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    if component is not None:
        mesh = component.static_mesh
        bounds_origin, bounds_extent = actor.get_actor_bounds(False)
        row.update({
            "static_mesh": mesh.get_path_name() if mesh else None,
            "actor_bounds_origin_cm": vec(bounds_origin),
            "actor_bounds_extent_cm": vec(bounds_extent),
            "collision_enabled": str(component.get_collision_enabled()),
            "collision_profile": str(component.get_collision_profile_name()),
            "can_affect_navigation": bool(component.get_editor_property("can_ever_affect_navigation")),
            "mobility": str(component.get_editor_property("mobility")),
        })
    rows.append(row)
    if "LBPR005Station" in class_path:
        native_station.append(row)

rows.sort(key=lambda item: item["label"])
payload = {
    "$schema": "cairnwell/audit/press-shop-pr005-v053-integration-datums/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "READ_ONLY_DATUM_INVENTORY__NO_PLACEMENT_AUTHORITY_INVENTED",
    "map": MAP,
    "match_count": len(rows),
    "native_station_count": len(native_station),
    "native_station": native_station,
    "matches": rows,
    "world_placement_rule": "Any enclosure successor must derive its transform from retained v053 PR005 actors; Candidate_v002 planning notation is not world-placement authority.",
    "map_modified": False,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({"status": payload["status"], "matches": len(rows), "native_station": len(native_station)}, indent=2))
