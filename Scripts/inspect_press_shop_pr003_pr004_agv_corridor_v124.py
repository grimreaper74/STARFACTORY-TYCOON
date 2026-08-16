"""Read-only audit of the proposed PR003/PR004 AGV corridor in retained v124."""

from pathlib import Path
import json
import unreal

MAP = "/Game/LineBoss/Maps/LB_PressShop_PR003Sheet2LayoutCandidate_v124"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr003_pr004_agv_corridor_inspection_v124.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

items = []
for actor in actors_api.get_all_level_actors():
    loc = actor.get_actor_location()
    rot = actor.get_actor_rotation()
    origin, extent = actor.get_actor_bounds(False, False)
    min_x, max_x = origin.x-extent.x, origin.x+extent.x
    min_y, max_y = origin.y-extent.y, origin.y+extent.y
    if max_x < -6150 or min_x > -4300 or max_y < -2850 or min_y > -1150:
        continue
    items.append({
        "label": actor.get_actor_label(), "class": actor.get_class().get_name(),
        "location_cm": [round(loc.x,2),round(loc.y,2),round(loc.z,2)],
        "rotation_deg": [round(rot.roll,2),round(rot.pitch,2),round(rot.yaw,2)],
        "bounds_min_cm": [round(min_x,2),round(min_y,2),round(origin.z-extent.z,2)],
        "bounds_max_cm": [round(max_x,2),round(max_y,2),round(origin.z+extent.z,2)],
        "hidden_game": bool(actor.get_editor_property("hidden")), "tags": [str(tag) for tag in actor.tags],
        "static_mesh": str(actor.static_mesh_component.static_mesh.get_path_name()) if isinstance(actor, unreal.StaticMeshActor) and actor.static_mesh_component.static_mesh else None,
    })
items.sort(key=lambda item: (item["bounds_min_cm"][0], item["bounds_min_cm"][1], item["label"]))
payload = {
    "$schema": "cairnwell/audit/press-shop-pr003-pr004-agv-corridor-inspection-v124/v1",
    "status": "READ_ONLY__NO_ASSETS_CHANGED", "map": MAP,
    "inspection_box_cm": {"x": [-6150,-4300], "y": [-2850,-1150]},
    "actor_count": len(items), "actors": items,
    "promotion_authorized": False,
}
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({"status":payload["status"],"actor_count":len(items),"out":str(OUT)}, indent=2))
