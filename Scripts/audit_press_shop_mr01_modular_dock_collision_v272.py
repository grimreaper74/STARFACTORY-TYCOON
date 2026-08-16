"""Read-only native structural-box collision ownership and overlap gate for v272."""
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v272"
OUT = Path(unreal.Paths.project_saved_dir()).resolve() / "Audits/SupportRobots/press_shop_mr01_modular_dock_collision_v272.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
actors = actors_api.get_all_level_actors()
by_label = {actor.get_actor_label(): actor for actor in actors}
dock = by_label.get("LB-DOCK-MR01-01")
if dock is None or dock.get_class().get_path_name() != "/Script/LineBossCarFactory.LBSupportRobotServiceDock":
    raise RuntimeError("native MR01-01 dock missing")

old_proxies = [
    "LB-DOCK-MR01-01_Collision_WestSide",
    "LB-DOCK-MR01-01_Collision_EastSide",
    "LB-DOCK-MR01-01_Collision_Rear",
]
old_proxy_absent = all(label not in by_label for label in old_proxies)
boxes = []
for component in dock.get_components_by_class(unreal.BoxComponent):
    name = component.get_name()
    if name not in {"StructuralLeft", "StructuralRight", "StructuralHeader"}:
        continue
    center = component.get_world_location()
    extent = component.get_unscaled_box_extent()
    scale = component.get_world_scale()
    extent = unreal.Vector(abs(extent.x * scale.x), abs(extent.y * scale.y), abs(extent.z * scale.z))
    boxes.append({
        "component": name,
        "collision": str(component.get_collision_enabled()),
        "profile": str(component.get_collision_profile_name()),
        "min": [center.x - extent.x, center.y - extent.y, center.z - extent.z],
        "max": [center.x + extent.x, center.y + extent.y, center.z + extent.z],
    })

ignored_tokens = ("floor", "roof", "ceiling", "liner", "zone_", "camera")
others = []
for actor in actors:
    if actor == dock or any(token in actor.get_actor_label().lower() for token in ignored_tokens):
        continue
    primitives = actor.get_components_by_class(unreal.PrimitiveComponent)
    if not any("NO_COLLISION" not in str(component.get_collision_enabled()) for component in primitives):
        continue
    origin, extent = actor.get_actor_bounds(True)
    if min(extent.x, extent.y, extent.z) <= 0.0:
        continue
    others.append({
        "label": actor.get_actor_label(),
        "min": [origin.x - extent.x, origin.y - extent.y, origin.z - extent.z],
        "max": [origin.x + extent.x, origin.y + extent.y, origin.z + extent.z],
    })

contacts = []
for box in boxes:
    for other in others:
        depth = [min(box["max"][axis], other["max"][axis]) - max(box["min"][axis], other["min"][axis]) for axis in range(3)]
        if min(depth) > 5.0:
            contacts.append({"component": box["component"], "other_actor": other["label"], "overlap_depth_cm": [round(value, 3) for value in depth]})

box_authority_pass = len(boxes) == 3 and all("NO_COLLISION" not in row["collision"] and row["profile"] == "BlockAll" for row in boxes)
passed = old_proxy_absent and box_authority_pass and not contacts
payload = {
    "$schema": "cairnwell/audit/press-shop-mr01-modular-dock-collision-v272/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__SINGLE_NATIVE_DOCK_COLLISION_OWNERSHIP__NO_UNEXPECTED_OVERLAPS__NOT_PROMOTED" if passed else "FAIL__NATIVE_DOCK_COLLISION_GATE__NOT_PROMOTED",
    "map": MAP,
    "old_proxy_blockers_absent": old_proxy_absent,
    "native_structural_boxes": boxes,
    "native_box_authority_pass": box_authority_pass,
    "unexpected_overlap_count": len(contacts),
    "unexpected_overlaps": contacts,
    "method": "Exact three native BoxComponent world AABBs versus inherited colliding-actor world AABBs; floor/roof/zone/camera excluded; <=5 cm adjacency ignored.",
    "read_only": True,
    "promotion_authorized": False
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({"status": payload["status"], "overlaps": len(contacts), "old_proxy_absent": old_proxy_absent}, indent=2))
unreal.SystemLibrary.quit_editor()
