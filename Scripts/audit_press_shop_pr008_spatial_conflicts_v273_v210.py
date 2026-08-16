"""List target and donor PR008 actors occupying the process-cell envelope."""
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAPS = {
    "target_v273": "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v273",
    "donor_v210": "/Game/LineBoss/Maps/LB_PressShop_PR008AuthoredAnchorCandidate_v210",
}
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_pr008_spatial_conflicts_v273_v210.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def in_envelope(actor):
    origin, extent = actor.get_actor_bounds(False)
    return (
        origin.x + extent.x >= -1450.0 and origin.x - extent.x <= 300.0
        and origin.y + extent.y >= -2600.0 and origin.y - extent.y <= -1400.0
        and origin.z + extent.z >= -20.0 and origin.z - extent.z <= 900.0
    )


maps = {}
for key, map_path in MAPS.items():
    if not levels.load_level(map_path):
        raise RuntimeError(map_path)
    rows = []
    for actor in actors_api.get_all_level_actors():
        if not isinstance(actor, unreal.StaticMeshActor) or not in_envelope(actor):
            continue
        component = actor.static_mesh_component
        mesh = component.static_mesh
        origin, extent = actor.get_actor_bounds(False)
        rows.append({
            "label": actor.get_actor_label(),
            "mesh": mesh.get_path_name() if mesh else None,
            "tags": [str(tag) for tag in actor.tags],
            "location": [actor.get_actor_location().x, actor.get_actor_location().y, actor.get_actor_location().z],
            "bounds_origin": [origin.x, origin.y, origin.z],
            "bounds_extent": [extent.x, extent.y, extent.z],
            "collision": str(component.get_collision_enabled()),
        })
    maps[key] = sorted(rows, key=lambda row: row["label"])

donor_labels = {row["label"] for row in maps["donor_v210"]}
target_only = [row for row in maps["target_v273"] if row["label"] not in donor_labels]
payload = {
    "$schema": "cairnwell/audit/press-shop-pr008-spatial-conflicts-v273-v210/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "maps": MAPS,
    "envelope_cm": {"x": [-1450, 300], "y": [-2600, -1400], "z": [-20, 900]},
    "counts": {key: len(rows) for key, rows in maps.items()},
    "target_only_count": len(target_only),
    "target_only": target_only,
    "all": maps,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({"counts": payload["counts"], "target_only_count": len(target_only)}, indent=2))
unreal.SystemLibrary.quit_editor()
