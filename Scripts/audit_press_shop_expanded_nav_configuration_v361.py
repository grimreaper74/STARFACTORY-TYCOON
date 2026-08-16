"""Read-only editor audit of v356 navigation configuration and dirtying scale."""
from datetime import datetime, timezone
import json
from pathlib import Path
import unreal

MAP = "/Game/LineBoss/Maps/LB_PressShop_ExpandedTrainPitchCandidate_v356"
ROOT = Path(unreal.Paths.project_dir())
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_expanded_nav_configuration_v361.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")


def vec(value):
    return [round(value.x, 3), round(value.y, 3), round(value.z, 3)]


rows = []
nav_affecting = 0
nav_affecting_movable = 0
nav_affecting_by_class = {}
for actor in actors_api.get_all_level_actors():
    actor_affecting = 0
    for comp in actor.get_components_by_class(unreal.PrimitiveComponent):
        try:
            affects = bool(comp.get_editor_property("can_ever_affect_navigation"))
        except Exception:
            affects = False
        if affects:
            actor_affecting += 1
            nav_affecting += 1
            try:
                mobility = str(comp.get_editor_property("mobility"))
            except Exception:
                mobility = "UNKNOWN"
            if "MOVABLE" in mobility.upper():
                nav_affecting_movable += 1
    if actor_affecting:
        cls = actor.get_class().get_name()
        nav_affecting_by_class[cls] = nav_affecting_by_class.get(cls, 0) + actor_affecting

for actor in actors_api.get_all_level_actors():
    if isinstance(actor, unreal.NavMeshBoundsVolume):
        origin, extent = actor.get_actor_bounds(False)
        rows.append({
            "label": actor.get_actor_label(),
            "location_cm": vec(actor.get_actor_location()),
            "bounds_origin_cm": vec(origin),
            "bounds_extent_cm": vec(extent),
            "bounds_size_cm": [round(extent.x * 2, 3), round(extent.y * 2, 3), round(extent.z * 2, 3)],
        })

recast_rows = []
for actor in actors_api.get_all_level_actors():
    if "RECASTNAVMESH" in actor.get_class().get_name().upper() or "RECASTNAVMESH" in actor.get_actor_label().upper():
        row = {"label": actor.get_actor_label(), "class": actor.get_class().get_name()}
        for prop in ("runtime_generation", "tile_size_uu", "cell_size", "cell_height", "agent_radius", "agent_height"):
            try:
                row[prop] = str(actor.get_editor_property(prop))
            except Exception:
                pass
        recast_rows.append(row)

payload = {
    "$schema": "cairnwell/audit/press-shop-expanded-nav-configuration-v361/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__READ_ONLY_NAV_CONFIGURATION_INVENTORY__NO_NAV_REBUILD",
    "map": MAP,
    "map_saved": False,
    "nav_bounds_count": len(rows),
    "nav_bounds": rows,
    "nav_affecting_primitive_components": nav_affecting,
    "nav_affecting_movable_components": nav_affecting_movable,
    "nav_affecting_components_by_actor_class": dict(sorted(nav_affecting_by_class.items(), key=lambda item: (-item[1], item[0]))),
    "recast_actors": recast_rows,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(json.dumps(payload, indent=2))
unreal.SystemLibrary.quit_editor()
