"""Resolve the exact v263 actor reported by the MR01 sweep."""

from datetime import datetime, timezone
import json
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v263"
OUT = ROOT / "Saved/Audits/SupportRobots/press_shop_static_mesh_actor_65_v263.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

rows = []
for actor in actors_api.get_all_level_actors():
    if actor.get_name() == "StaticMeshActor_65" or actor.get_actor_label() == "StaticMeshActor_65":
        origin, extent = actor.get_actor_bounds(False, False)
        component = actor.get_component_by_class(unreal.StaticMeshComponent)
        rows.append({
            "name": actor.get_name(), "label": actor.get_actor_label(),
            "class": actor.get_class().get_name(), "tags": [str(tag) for tag in actor.tags],
            "location_cm": [actor.get_actor_location().x, actor.get_actor_location().y, actor.get_actor_location().z],
            "bounds_origin_cm": [origin.x, origin.y, origin.z],
            "bounds_size_cm": [extent.x * 2.0, extent.y * 2.0, extent.z * 2.0],
            "mesh": component.get_editor_property("static_mesh").get_path_name() if component and component.get_editor_property("static_mesh") else None,
            "collision_profile": str(component.get_collision_profile_name()) if component else None,
            "collision_enabled": str(component.get_editor_property("body_instance").get_editor_property("collision_enabled")) if component else None,
        })
payload = {"$schema": "cairnwell/audit/resolve-static-mesh-actor-65-v263/v1",
           "generated_utc": datetime.now(timezone.utc).isoformat(), "map": MAP, "matches": rows}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(json.dumps(payload, indent=2))
unreal.SystemLibrary.quit_editor()
