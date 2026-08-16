"""Read-only inventory of PR009/PR010 navigation actors in v240."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v240"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/PressShopIntegration/press_shop_pr009_pr010_navigation_actors_v240.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)

rows = []
for actor in actors_api.get_all_level_actors():
    tags = [str(value) for value in actor.tags]
    label = actor.get_actor_label()
    if not (isinstance(actor, (unreal.NavMeshBoundsVolume, unreal.NavModifierVolume, unreal.RecastNavMesh))
            or "Navigation" in label or any("Navigation" in tag for tag in tags)):
        continue
    origin, extent = actor.get_actor_bounds(False, False)
    row = {
        "label": label,
        "class": actor.get_class().get_name(),
        "location_cm": [actor.get_actor_location().x, actor.get_actor_location().y, actor.get_actor_location().z],
        "size_cm": [extent.x * 2.0, extent.y * 2.0, extent.z * 2.0],
        "scale": [actor.get_actor_scale3d().x, actor.get_actor_scale3d().y, actor.get_actor_scale3d().z],
        "tags": tags,
    }
    if isinstance(actor, unreal.NavModifierVolume):
        area = actor.get_editor_property("area_class")
        row["area_class"] = area.get_path_name() if area else None
    rows.append(row)

payload = {
    "$schema": "cairnwell/audit/press-shop-pr009-pr010-navigation-actors-v240/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "READ_ONLY__NO_ASSETS_CHANGED",
    "map": MAP,
    "actor_count": len(rows),
    "actors": sorted(rows, key=lambda row: (row["class"], row["label"])),
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({"actor_count": len(rows), "actors": [row["label"] for row in payload["actors"]]}, indent=2))
unreal.SystemLibrary.quit_editor()

