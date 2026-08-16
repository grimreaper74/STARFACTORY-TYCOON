"""Read-only Unreal inspection of actual CR01/MR01 authorities for dock alignment."""

from datetime import datetime, timezone
import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Developer/Validation/LB_ServiceDockFamilyVisual_v005"
OUT = ROOT / "Saved/Audits/SupportRobots/service_dock_actual_robot_fit_inputs_v001.json"
BP_PATHS = {
    "MR01": "/Game/LineBoss/Robots/Maintenance/MR01/Candidate_v021/Blueprints/BP_LB_MR01_MaintenanceAMR_v021",
    "CR01": "/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v065/Blueprints/BP_LB_CR01_CleaningAMR_v065",
}

lib = unreal.EditorAssetLibrary
blueprints = unreal.BlueprintEditorLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def vector(value):
    return [round(value.x, 4), round(value.y, 4), round(value.z, 4)]


def rotator(value):
    return [round(value.roll, 4), round(value.pitch, 4), round(value.yaw, 4)]


if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load preserved fit-input map {MAP}")

rows = {}
spawned = []
for index, (family, path) in enumerate(BP_PATHS.items()):
    bp = lib.load_asset(path)
    if not isinstance(bp, unreal.Blueprint):
        raise RuntimeError(f"Missing actual retained authority {path}")
    generated = blueprints.generated_class(bp)
    actor = actors_api.spawn_actor_from_class(generated, unreal.Vector(index * 500.0, 0.0, 0.0), unreal.Rotator())
    if actor is None:
        raise RuntimeError(f"Could not spawn {family}")
    spawned.append(actor)
    origin, extent = actor.get_actor_bounds(False)
    components = []
    for component in actor.get_components_by_class(unreal.SceneComponent):
        name = component.get_name()
        tags = [str(tag) for tag in component.get_editor_property("component_tags")]
        if "Dock" not in name and not any("Dock" in tag for tag in tags) and not isinstance(component, unreal.ChildActorComponent):
            continue
        components.append({
            "name": name,
            "class": component.get_class().get_name(),
            "relative_location_cm": vector(component.get_editor_property("relative_location")),
            "relative_rotation_deg": rotator(component.get_editor_property("relative_rotation")),
            "world_location_cm": vector(component.get_world_location()),
            "tags": tags,
        })
    child_rows = []
    for component in actor.get_components_by_class(unreal.ChildActorComponent):
        child = component.get_editor_property("child_actor")
        if child is None:
            continue
        child_origin, child_extent = child.get_actor_bounds(False)
        child_rows.append({
            "component": component.get_name(),
            "child_class": child.get_class().get_name(),
            "origin_cm": vector(child_origin),
            "extent_cm": vector(child_extent),
            "size_cm": vector(child_extent * 2.0),
        })
    rows[family] = {
        "blueprint": path,
        "actor_class": actor.get_class().get_name(),
        "actor_bounds_origin_cm": vector(origin),
        "actor_bounds_extent_cm": vector(extent),
        "actor_bounds_size_cm": vector(extent * 2.0),
        "dock_related_components": components,
        "presentation_children": child_rows,
    }

for actor in spawned:
    actors_api.destroy_actor(actor)

payload = {
    "$schema": "cairnwell/audit/service-dock-actual-robot-fit-inputs-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__READ_ONLY_ACTUAL_RETAINED_ROBOT_AUTHORITY_INPUTS_CAPTURED__NO_MAP_SAVED",
    "map_loaded_not_saved": MAP,
    "robots": rows,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
unreal.log(f"LINE_BOSS_SERVICE_DOCK_ACTUAL_ROBOT_INPUTS_PASS audit={OUT}")
