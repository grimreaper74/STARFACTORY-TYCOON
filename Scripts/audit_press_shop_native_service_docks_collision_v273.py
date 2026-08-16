"""Read-only collision ownership and overlap gate for all four native v273 docks."""
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v273"
OUT = Path(unreal.Paths.project_saved_dir()).resolve() / "Audits/SupportRobots/press_shop_native_service_docks_collision_v273.json"
DOCKS = ["LB-DOCK-MR01-01", "LB-DOCK-MR01-02", "LB-DOCK-CR01-01", "LB-DOCK-CR01-02"]
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
actors = actors_api.get_all_level_actors()
by_label = {actor.get_actor_label(): actor for actor in actors}
native = [by_label.get(label) for label in DOCKS]
if any(actor is None or actor.get_class().get_path_name() != "/Script/LineBossCarFactory.LBSupportRobotServiceDock" for actor in native):
    raise RuntimeError("one or more native docks missing")

old_proxies = [f"{label}_{suffix}" for label in DOCKS for suffix in ("Collision_WestSide", "Collision_EastSide", "Collision_Rear")]
old_proxy_absent = all(label not in by_label for label in old_proxies)
boxes = []
for dock in native:
    for component in dock.get_components_by_class(unreal.BoxComponent):
        if component.get_name() not in {"StructuralLeft", "StructuralRight", "StructuralHeader"}:
            continue
        center = component.get_world_location()
        extent = component.get_unscaled_box_extent()
        scale = component.get_world_scale()
        extent = unreal.Vector(abs(extent.x * scale.x), abs(extent.y * scale.y), abs(extent.z * scale.z))
        boxes.append({
            "dock": dock.get_actor_label(), "component": component.get_name(),
            "collision": str(component.get_collision_enabled()), "profile": str(component.get_collision_profile_name()),
            "min": [center.x - extent.x, center.y - extent.y, center.z - extent.z],
            "max": [center.x + extent.x, center.y + extent.y, center.z + extent.z],
        })

ignored_tokens = ("floor", "roof", "ceiling", "liner", "zone_", "camera")
others = []
for actor in actors:
    if actor in native or any(token in actor.get_actor_label().lower() for token in ignored_tokens):
        continue
    primitives = actor.get_components_by_class(unreal.PrimitiveComponent)
    if not any("NO_COLLISION" not in str(component.get_collision_enabled()) for component in primitives):
        continue
    origin, extent = actor.get_actor_bounds(True)
    if min(extent.x, extent.y, extent.z) <= 0:
        continue
    others.append({"label": actor.get_actor_label(), "min": [origin.x-extent.x, origin.y-extent.y, origin.z-extent.z], "max": [origin.x+extent.x, origin.y+extent.y, origin.z+extent.z]})

contacts = []
for box in boxes:
    for other in others:
        depth = [min(box["max"][axis], other["max"][axis]) - max(box["min"][axis], other["min"][axis]) for axis in range(3)]
        if min(depth) > 5:
            contacts.append({"dock": box["dock"], "component": box["component"], "other_actor": other["label"], "overlap_depth_cm": [round(v,3) for v in depth]})
for index, box in enumerate(boxes):
    for other in boxes[index+1:]:
        if box["dock"] == other["dock"]:
            continue
        depth = [min(box["max"][axis], other["max"][axis]) - max(box["min"][axis], other["min"][axis]) for axis in range(3)]
        if min(depth) > 5:
            contacts.append({"dock": box["dock"], "component": box["component"], "other_actor": f"{other['dock']}:{other['component']}", "overlap_depth_cm": [round(v,3) for v in depth]})

authority_pass = len(boxes) == 12 and all("NO_COLLISION" not in row["collision"] and row["profile"] == "BlockAll" for row in boxes)
passed = old_proxy_absent and authority_pass and not contacts
payload = {
    "$schema": "cairnwell/audit/press-shop-native-service-docks-collision-v273/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__FOUR_NATIVE_DOCK_COLLISION_OWNERSHIP__NO_UNEXPECTED_OVERLAPS__NOT_PROMOTED" if passed else "FAIL__FOUR_NATIVE_DOCK_COLLISION_GATE__NOT_PROMOTED",
    "map": MAP, "old_proxy_blockers_absent": old_proxy_absent,
    "native_structural_box_count": len(boxes), "expected_native_structural_box_count": 12,
    "native_box_authority_pass": authority_pass, "unexpected_overlap_count": len(contacts), "unexpected_overlaps": contacts,
    "native_structural_boxes": boxes, "read_only": True, "promotion_authorized": False
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({"status": payload["status"], "boxes": len(boxes), "overlaps": len(contacts), "old_proxy_absent": old_proxy_absent}, indent=2))
unreal.SystemLibrary.quit_editor()
