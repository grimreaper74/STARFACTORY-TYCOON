"""Conservative read-only support-area collision screen for v250."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v250"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/PressShopIntegration/press_shop_support_collision_v250.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)


def record(actor):
    if not isinstance(actor, unreal.StaticMeshActor):
        return None
    component = actor.static_mesh_component
    if component.get_collision_enabled() == unreal.CollisionEnabled.NO_COLLISION:
        return None
    origin, extent = actor.get_actor_bounds(False)
    return {
        "label": actor.get_actor_label(),
        "tags": [str(tag) for tag in actor.tags],
        "min": [origin.x - extent.x, origin.y - extent.y, origin.z - extent.z],
        "max": [origin.x + extent.x, origin.y + extent.y, origin.z + extent.z],
    }


all_rows = [row for row in (record(actor) for actor in actors_api.get_all_level_actors()) if row]
support = [row for row in all_rows if "LB.Asset.CandidateNotPromoted" in row["tags"]
           and any(tag.startswith("LB.SupportArea.") for tag in row["tags"])]
inherited = [row for row in all_rows if row not in support]
ignored_environment_tokens = ("LB_PRESS_Floor", "LB_ZONE_", "Roof", "Ceiling", "Liner")
contacts = []
for item in support:
    for other in inherited:
        if any(token.lower() in other["label"].lower() for token in ignored_environment_tokens):
            continue
        depth = [min(item["max"][axis], other["max"][axis]) -
                 max(item["min"][axis], other["min"][axis]) for axis in range(3)]
        if min(depth) <= 5.0:
            continue
        contacts.append({
            "support_actor": item["label"],
            "inherited_actor": other["label"],
            "overlap_depth_cm": [round(value, 3) for value in depth],
            "overlap_volume_cm3": round(depth[0] * depth[1] * depth[2], 3),
        })
contacts.sort(key=lambda row: row["overlap_volume_cm3"], reverse=True)
payload = {
    "$schema": "cairnwell/audit/press-shop-support-collision-v250/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__NO_SUPPORT_TO_INHERITED_BLOCKER_AABB_OVERLAPS" if not contacts else "REVIEW__SUPPORT_TO_INHERITED_BLOCKER_AABB_OVERLAPS",
    "map": MAP,
    "support_blocker_count": len(support),
    "inherited_blocker_count": len(inherited),
    "overlap_pair_count": len(contacts),
    "overlaps": contacts,
    "method": "Conservative world-axis bounds screen; floor, zone slab and roof/liner contacts excluded.",
    "read_only": True,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({key: payload[key] for key in ("status", "support_blocker_count", "inherited_blocker_count", "overlap_pair_count")}, indent=2))
unreal.SystemLibrary.quit_editor()
