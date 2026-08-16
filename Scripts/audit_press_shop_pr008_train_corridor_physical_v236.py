"""Read-only spatial inventory between PR008 and the installed press trains."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v236"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_pr008_train_corridor_physical_v236.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)

rows = []
for actor in actors_api.get_all_level_actors():
    if not isinstance(actor, (unreal.StaticMeshActor, unreal.SkeletalMeshActor, unreal.TextRenderActor)):
        continue
    origin, extent = actor.get_actor_bounds(False)
    # Existing-map corridor only: from PR008's west edge to the first train
    # datum, with enough cross-flow width to include stack/dock equipment.
    if origin.x + extent.x < -1100.0 or origin.x - extent.x > 1700.0:
        continue
    if origin.y + extent.y < -3300.0 or origin.y - extent.y > -700.0:
        continue
    label = actor.get_actor_label()
    tags = [str(tag) for tag in actor.tags]
    if label.startswith("LB_PRESS_Column_") or "LB.Module.FactoryRoofLiner" in tags:
        continue
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    mesh = component.get_editor_property("static_mesh") if component else None
    rows.append({
        "label": label,
        "class": actor.get_class().get_name(),
        "mesh": mesh.get_path_name() if mesh else None,
        "origin_cm": [origin.x, origin.y, origin.z],
        "extent_cm": [extent.x, extent.y, extent.z],
        "bounds_min_cm": [origin.x - extent.x, origin.y - extent.y, origin.z - extent.z],
        "bounds_max_cm": [origin.x + extent.x, origin.y + extent.y, origin.z + extent.z],
        "tags": tags,
    })

rows.sort(key=lambda row: (row["origin_cm"][0], row["origin_cm"][1], row["label"]))
payload = {
    "$schema": "cairnwell/audit/press-shop-pr008-train-corridor-physical-v236/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "READ_ONLY__NO_ASSETS_CHANGED",
    "map": MAP,
    "corridor_cm": {"x": [-1100.0, 1700.0], "y": [-3300.0, -700.0]},
    "physical_actor_count": len(rows),
    "actors": rows,
    "placement_authority": "EXISTING_MAP_ONLY__NO_NEW_DATUMS_INVENTED",
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({"status": payload["status"], "physical_actor_count": len(rows),
                  "labels": [row["label"] for row in rows]}, indent=2))
unreal.SystemLibrary.quit_editor()
