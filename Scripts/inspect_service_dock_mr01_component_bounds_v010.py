"""Read-only component-bound decomposition for docked MR01 v021."""

from datetime import datetime, timezone
import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Developer/Validation/LB_ServiceDockActualRobotFit_v008"
OUT = ROOT / "Saved/Audits/SupportRobots/service_dock_mr01_component_bounds_v010.json"
ACTORS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def vec(value):
    return [round(value.x, 4), round(value.y, 4), round(value.z, 4)]


world = unreal.EditorLevelLibrary.get_editor_world()
current = world.get_outermost().get_name() if world is not None else ""
if current != MAP:
    raise RuntimeError("One-map rule violation: opened {}, expected {}".format(current, MAP))
mr = {actor.get_actor_label(): actor for actor in ACTORS.get_all_level_actors()}.get(
    "LB_DOCK_FIT_MR01_v021_ActualAuthority"
)
if mr is None:
    raise RuntimeError("Docked MR01 authority missing")

rows = []
for item in mr.get_components_by_class(unreal.PrimitiveComponent):
    try:
        origin, extent, radius = unreal.SystemLibrary.get_component_bounds(item)
        row = {
            "name": item.get_name(),
            "class": item.get_class().get_name(),
            "tags": sorted(str(tag) for tag in item.get_editor_property("component_tags")),
            "visible": bool(item.is_visible()),
            "hidden_in_game": bool(item.get_editor_property("hidden_in_game")),
            "collision_enabled": str(item.get_collision_enabled()),
            "bounds_origin_cm": vec(origin),
            "bounds_size_cm": vec(extent * 2.0),
            "sphere_radius_cm": round(radius, 4),
        }
    except Exception as exc:
        row = {
            "name": item.get_name(),
            "class": item.get_class().get_name(),
            "error": str(exc),
        }
    rows.append(row)

rows.sort(key=lambda row: row.get("bounds_size_cm", [0.0])[0], reverse=True)
actor_origin, actor_extent = mr.get_actor_bounds(False)
payload = {
    "$schema": "cairnwell/audit/service-dock-mr01-component-bounds-v010/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__READ_ONLY_COMPONENT_BOUNDS_DECOMPOSED__ENGINEERING_REVIEW_REQUIRED",
    "source_map_loaded_not_saved": MAP,
    "actor": mr.get_actor_label(),
    "actor_bounds_origin_cm": vec(actor_origin),
    "actor_bounds_size_cm": vec(actor_extent * 2.0),
    "primitive_component_count": len(rows),
    "components": rows,
    "map_saved": False,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
unreal.log("LINE_BOSS_MR01_COMPONENT_BOUNDS_V010 count={}".format(len(rows)))
