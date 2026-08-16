"""Inventory visible actors intersecting the PR-008 envelope for isolated v075 cleanup."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR008NativeRuntimeCandidate_v074"
OUT = ROOT / "Saved/Audits/press_shop_pr008_visual_obstructions_v074.json"
STATION_MIN = unreal.Vector(-1020.0, -2280.0, -5.0)
STATION_MAX = unreal.Vector(25.0, -1720.0, 455.0)

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")


def intersects(a_min, a_max):
    return not (
        a_max.x < STATION_MIN.x or a_min.x > STATION_MAX.x
        or a_max.y < STATION_MIN.y or a_min.y > STATION_MAX.y
        or a_max.z < STATION_MIN.z or a_min.z > STATION_MAX.z
    )


rows = []
for actor in actors_api.get_all_level_actors():
    origin, extent = actor.get_actor_bounds(False, False)
    a_min = unreal.Vector(origin.x - extent.x, origin.y - extent.y, origin.z - extent.z)
    a_max = unreal.Vector(origin.x + extent.x, origin.y + extent.y, origin.z + extent.z)
    is_pr008_text = isinstance(actor, unreal.TextRenderActor) and "PR008" in actor.get_actor_label().upper()
    if not intersects(a_min, a_max) and not is_pr008_text:
        continue
    label = actor.get_actor_label()
    component = actor.static_mesh_component if isinstance(actor, unreal.StaticMeshActor) else None
    mesh_path = None
    visible = True
    collision = None
    if component:
        mesh = component.static_mesh
        mesh_path = mesh.get_path_name() if mesh else None
        visible = bool(component.get_editor_property("visible"))
        collision = str(component.get_collision_enabled())
    rendered_text = None
    if isinstance(actor, unreal.TextRenderActor):
        rendered_text = str(actor.text_render.get_editor_property("text"))
    rows.append({
        "actor": label,
        "class": actor.get_class().get_name(),
        "location_cm": [actor.get_actor_location().x, actor.get_actor_location().y, actor.get_actor_location().z],
        "bounds_min_cm": [a_min.x, a_min.y, a_min.z],
        "bounds_max_cm": [a_max.x, a_max.y, a_max.z],
        "extent_cm": [extent.x, extent.y, extent.z],
        "hidden": bool(actor.get_editor_property("hidden")),
        "component_visible": visible,
        "collision": collision,
        "mesh": mesh_path,
        "rendered_text": rendered_text,
        "tags": [str(tag) for tag in actor.tags],
        "likely_planning_or_placeholder": any(token in label.upper() for token in (
            "ENV_", "ENVELOPE", "PLANNING", "CAGE", "PLACEHOLDER", "BLOCKOUT",
        )),
    })

rows.sort(key=lambda row: row["actor"])
payload = {
    "$schema": "line-boss/audit/press-shop-pr008-visual-obstructions-v074/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "map": MAP,
    "station_query_min_cm": [STATION_MIN.x, STATION_MIN.y, STATION_MIN.z],
    "station_query_max_cm": [STATION_MAX.x, STATION_MAX.y, STATION_MAX.z],
    "intersecting_actor_count": len(rows),
    "likely_planning_or_placeholder_count": sum(1 for row in rows if row["likely_planning_or_placeholder"]),
    "actors": rows,
    "note": "Read-only inventory. No actor is approved for removal solely by this audit.",
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR008_V074_VISUAL_OBSTRUCTION_INVENTORY actors={len(rows)}")
unreal.SystemLibrary.quit_editor()
