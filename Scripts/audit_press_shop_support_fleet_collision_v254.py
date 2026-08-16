"""Conservative read-only collision screen for the four v254 support berths."""

from datetime import datetime, timezone
import json
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v254"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/SupportRobots/press_shop_support_fleet_collision_v254.json"
LEVELS = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTORS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if not LEVELS.load_level(MAP):
    raise RuntimeError(MAP)


def colliding_bounds(actor):
    has_collision = False
    for component in actor.get_components_by_class(unreal.PrimitiveComponent):
        if component.get_collision_enabled() != unreal.CollisionEnabled.NO_COLLISION:
            has_collision = True
            break
    if not has_collision:
        return None
    origin, extent = actor.get_actor_bounds(True)
    if extent.x <= 0.0 or extent.y <= 0.0 or extent.z <= 0.0:
        return None
    return {
        "label": actor.get_actor_label(),
        "tags": [str(tag) for tag in actor.tags],
        "min": [origin.x - extent.x, origin.y - extent.y, origin.z - extent.z],
        "max": [origin.x + extent.x, origin.y + extent.y, origin.z + extent.z],
    }


rows = [row for row in (colliding_bounds(actor) for actor in ACTORS.get_all_level_actors()) if row]
fleet = [row for row in rows if any(
    tag.startswith("LB.SupportRobot.") or tag == "LB.Collision.Proxy.Provisional"
    for tag in row["tags"]
)]
inherited = [row for row in rows if row not in fleet]
ignored_environment_tokens = ("LB_PRESS_Floor", "LB_ZONE_", "Roof", "Ceiling", "Liner")


def overlap(a, b):
    depth = [min(a["max"][axis], b["max"][axis]) - max(a["min"][axis], b["min"][axis])
             for axis in range(3)]
    if min(depth) <= 5.0:
        return None
    return [round(value, 3) for value in depth]


contacts = []
for item in fleet:
    for other in inherited:
        if any(token.lower() in other["label"].lower() for token in ignored_environment_tokens):
            continue
        depth = overlap(item, other)
        if depth:
            contacts.append({
                "fleet_actor": item["label"],
                "other_actor": other["label"],
                "overlap_depth_cm": depth,
                "classification": "UNEXPECTED_FLEET_TO_INHERITED",
            })
for index, item in enumerate(fleet):
    for other in fleet[index + 1:]:
        depth = overlap(item, other)
        if depth:
            contacts.append({
                "fleet_actor": item["label"],
                "other_actor": other["label"],
                "overlap_depth_cm": depth,
                "classification": "UNEXPECTED_FLEET_INTERNAL",
            })

payload = {
    "$schema": "cairnwell/audit/press-shop-support-fleet-collision-v254/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__NO_UNEXPECTED_SUPPORT_FLEET_BLOCKER_AABB_OVERLAPS" if not contacts else "REVIEW__SUPPORT_FLEET_BLOCKER_AABB_OVERLAPS",
    "map": MAP,
    "fleet_blocker_count": len(fleet),
    "inherited_blocker_count": len(inherited),
    "overlap_pair_count": len(contacts),
    "overlaps": contacts,
    "method": "Conservative colliding-component world AABB screen; floor, zone slab and roof/liner contacts excluded; contacts <=5 cm treated as adjacency.",
    "read_only": True,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(json.dumps({key: payload[key] for key in ("status", "fleet_blocker_count", "inherited_blocker_count", "overlap_pair_count")}, indent=2))
unreal.SystemLibrary.quit_editor()
