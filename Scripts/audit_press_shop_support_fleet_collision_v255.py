"""Read-only collision and collision-ownership gate for corrected v255."""

from datetime import datetime, timezone
import json
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v255"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/SupportRobots/press_shop_support_fleet_collision_v255.json"
LEVELS = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTORS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if not LEVELS.load_level(MAP):
    raise RuntimeError(MAP)


def primitive_rows(actor):
    result = []
    for component in actor.get_components_by_class(unreal.PrimitiveComponent):
        result.append({
            "name": component.get_name(),
            "collision": str(component.get_collision_enabled()),
            "profile": str(component.get_collision_profile_name()),
        })
    return result


def colliding_bounds(actor):
    components = primitive_rows(actor)
    if not any("NO_COLLISION" not in row["collision"] for row in components):
        return None
    origin, extent = actor.get_actor_bounds(True)
    if min(extent.x, extent.y, extent.z) <= 0.0:
        return None
    return {
        "label": actor.get_actor_label(),
        "tags": [str(tag) for tag in actor.tags],
        "min": [origin.x - extent.x, origin.y - extent.y, origin.z - extent.z],
        "max": [origin.x + extent.x, origin.y + extent.y, origin.z + extent.z],
    }


actors = ACTORS.get_all_level_actors()
by_label = {actor.get_actor_label(): actor for actor in actors}
dock_visuals = [by_label.get(label) for label in (
    "LB-DOCK-MR01-01", "LB-DOCK-MR01-02", "LB-DOCK-CR01-01", "LB-DOCK-CR01-02")]
if any(actor is None for actor in dock_visuals):
    raise RuntimeError("One or more v255 dock visuals are missing")
dock_visual_collision = {
    actor.get_actor_label(): primitive_rows(actor) for actor in dock_visuals
}
dock_visual_no_collision = all(
    all("NO_COLLISION" in row["collision"] for row in rows)
    for rows in dock_visual_collision.values()
)

child_presentations = [actor for actor in actors if actor.get_actor_label().startswith("BP_LB_CR01_CleaningAMR_v064")]
child_collision = {actor.get_actor_label(): primitive_rows(actor) for actor in child_presentations}
child_no_collision = len(child_presentations) == 2 and all(
    all("NO_COLLISION" in row["collision"] for row in rows)
    for rows in child_collision.values()
)

rows = [row for row in (colliding_bounds(actor) for actor in actors) if row]
fleet = [row for row in rows if (
    "LB.SupportRobot.MR01" in row["tags"]
    or "LB.SupportRobot.CR01" in row["tags"]
    or "LB.Collision.Proxy.Provisional" in row["tags"]
)]
inherited = [row for row in rows if row not in fleet]
ignored_environment_tokens = (
    "LB_PRESS_Floor", "FinishedFloor", "LB_ZONE_", "Roof", "Ceiling", "Liner")


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
            contacts.append({"fleet_actor": item["label"], "other_actor": other["label"], "overlap_depth_cm": depth})
for index, item in enumerate(fleet):
    for other in fleet[index + 1:]:
        depth = overlap(item, other)
        if depth:
            contacts.append({"fleet_actor": item["label"], "other_actor": other["label"], "overlap_depth_cm": depth})

passed = not contacts and dock_visual_no_collision and child_no_collision and len(fleet) == 16
payload = {
    "$schema": "cairnwell/audit/press-shop-support-fleet-collision-v255/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__CLEAN_COLLISION_OWNERSHIP_AND_NO_UNEXPECTED_FLEET_AABB_OVERLAPS" if passed else "FAIL__SUPPORT_FLEET_COLLISION_GATE__NOT_RETAINED",
    "map": MAP,
    "fleet_blocker_count": len(fleet),
    "expected_fleet_blocker_count": 16,
    "inherited_blocker_count": len(inherited),
    "overlap_pair_count": len(contacts),
    "overlaps": contacts,
    "dock_visual_no_collision": dock_visual_no_collision,
    "dock_visual_components": dock_visual_collision,
    "cr01_child_presentation_count": len(child_presentations),
    "cr01_child_presentations_no_collision": child_no_collision,
    "cr01_child_components": child_collision,
    "method": "Explicit ownership audit plus conservative colliding-component world AABB screen; grounded floor/zone/roof contacts excluded; <=5 cm adjacency ignored.",
    "read_only": True,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(json.dumps({key: payload[key] for key in (
    "status", "fleet_blocker_count", "overlap_pair_count", "dock_visual_no_collision", "cr01_child_presentations_no_collision")}, indent=2))
unreal.SystemLibrary.quit_editor()
