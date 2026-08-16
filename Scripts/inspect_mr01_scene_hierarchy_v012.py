"""Read-only MR01 runtime scene hierarchy audit for the rejected dock-fit v008 map.

The script never saves the loaded map.  It records attachment parents and local/world
transforms so the imported presentation can be realigned to the native collision and
docking authority in a fresh, non-overwriting Blueprint successor.
"""

from datetime import datetime, timezone
import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Developer/Validation/LB_ServiceDockActualRobotFit_v008"
OUT = ROOT / "Saved/Audits/SupportRobots/mr01_scene_hierarchy_v012.json"
ACTOR_LABEL = "LB_DOCK_FIT_MR01_v021_ActualAuthority"
ACTORS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def vec(value):
    return [round(float(value.x), 4), round(float(value.y), 4), round(float(value.z), 4)]


def rot(value):
    return [round(float(value.roll), 4), round(float(value.pitch), 4), round(float(value.yaw), 4)]


def component_tags(component):
    try:
        return [str(tag) for tag in component.get_editor_property("component_tags")]
    except Exception:
        return []


world = unreal.EditorLevelLibrary.get_editor_world()
current_map = world.get_outermost().get_name() if world is not None else ""
if current_map != MAP:
    raise RuntimeError("One-map rule violation: opened {}, expected {}".format(current_map, MAP))

actors = {actor.get_actor_label(): actor for actor in ACTORS.get_all_level_actors()}
mr01 = actors.get(ACTOR_LABEL)
if mr01 is None:
    raise RuntimeError("Missing {}".format(ACTOR_LABEL))

rows = []
for component in mr01.get_components_by_class(unreal.SceneComponent):
    parent = component.get_attach_parent()
    row = {
        "name": component.get_name(),
        "class": component.get_class().get_name(),
        "parent": parent.get_name() if parent is not None else None,
        "relative_location_cm": vec(component.get_editor_property("relative_location")),
        "relative_rotation_roll_pitch_yaw_deg": rot(component.get_editor_property("relative_rotation")),
        "world_location_cm": vec(component.get_world_location()),
        "world_rotation_roll_pitch_yaw_deg": rot(component.get_world_rotation()),
        "tags": component_tags(component),
    }
    if isinstance(component, unreal.PrimitiveComponent):
        origin, extent, _radius = unreal.SystemLibrary.get_component_bounds(component)
        row["bounds_origin_cm"] = vec(origin)
        row["bounds_size_cm"] = vec(extent * 2.0)
        row["visible"] = bool(component.is_visible())
        try:
            row["hidden_in_game"] = bool(component.get_editor_property("hidden_in_game"))
        except Exception:
            row["hidden_in_game"] = False
    rows.append(row)

rows.sort(key=lambda item: (item["parent"] or "", item["name"]))
by_name = {row["name"]: row for row in rows}


def chain(name):
    result = []
    seen = set()
    current = name
    while current and current not in seen:
        seen.add(current)
        row = by_name.get(current)
        if row is None:
            result.append({"name": current, "missing_from_scene_rows": True})
            break
        result.append({
            "name": row["name"],
            "class": row["class"],
            "parent": row["parent"],
            "relative_location_cm": row["relative_location_cm"],
            "relative_rotation_roll_pitch_yaw_deg": row["relative_rotation_roll_pitch_yaw_deg"],
            "tags": row["tags"],
        })
        current = row["parent"]
    return result


focus_names = [
    "Visual_SM_LB_MR01_BumperFront",
    "Visual_SM_LB_MR01_BumperRear",
    "Visual_SM_LB_MR01_BumperSide_L",
    "Visual_SM_LB_MR01_BumperSide_R",
    "Visual_MR01_ArmPoseable",
    "RP01_CollisionRoot",
    "RobotVisualRoot",
]
focus = {name: chain(name) for name in focus_names if name in by_name}

top_level_presentation = [
    row["name"]
    for row in rows
    if (row["name"].startswith("Visual_") or any(tag.startswith("LB.MR01") for tag in row["tags"]))
    and (row["parent"] is None or not (row["parent"].startswith("Visual_") or row["parent"] in by_name))
]

payload = {
    "$schema": "cairnwell/audit/mr01-scene-hierarchy-v012/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__READ_ONLY_RUNTIME_HIERARCHY_RECORDED__NO_ASSET_SAVED",
    "source_map_loaded_not_saved": MAP,
    "actor": ACTOR_LABEL,
    "actor_class": mr01.get_class().get_path_name(),
    "actor_rotation_roll_pitch_yaw_deg": rot(mr01.get_actor_rotation()),
    "scene_component_count": len(rows),
    "focus_parent_chains": focus,
    "top_level_presentation_candidates": top_level_presentation,
    "components": rows,
    "map_saved": False,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
unreal.log("LINE_BOSS_MR01_SCENE_HIERARCHY_V012 {}".format(payload["status"]))
