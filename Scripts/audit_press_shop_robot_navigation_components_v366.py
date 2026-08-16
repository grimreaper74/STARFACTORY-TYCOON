"""Read-only component-level navigation/collision inventory on v362 robots."""
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import unreal

MAP = "/Game/LineBoss/Maps/LB_PressShop_ExpandedTrainNavCandidate_v362"
ROOT = Path(unreal.Paths.project_dir())
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_robot_navigation_components_v366.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)

rows = []
summary = Counter()
for actor in actors.get_all_level_actors():
    cls = actor.get_class().get_name()
    if not any(token in cls for token in ("MaintenanceAMR", "CleaningAMR")):
        continue
    components = []
    for comp in actor.get_components_by_class(unreal.PrimitiveComponent):
        try:
            affects = bool(comp.get_editor_property("can_ever_affect_navigation"))
        except Exception:
            affects = False
        collision = str(comp.get_collision_enabled())
        mobility = str(comp.get_editor_property("mobility"))
        key = (cls, affects, collision, mobility, comp.get_class().get_name())
        summary[key] += 1
        if affects:
            components.append({"name": comp.get_name(), "class": comp.get_class().get_name(),
                               "collision_enabled": collision, "mobility": mobility,
                               "generate_overlap_events": bool(comp.get_editor_property("generate_overlap_events"))})
    rows.append({"actor": actor.get_actor_label(), "class": cls,
                 "nav_affecting_component_count": len(components), "nav_affecting_components": components})

payload = {"$schema": "cairnwell/audit/press-shop-robot-navigation-components-v366/v1",
           "generated_utc": datetime.now(timezone.utc).isoformat(),
           "status": "PASS__READ_ONLY_ROBOT_NAVIGATION_COMPONENT_INVENTORY",
           "map": MAP, "map_saved": False, "actors": rows,
           "summary": [{"actor_class": key[0], "affects_navigation": key[1],
                        "collision_enabled": key[2], "mobility": key[3],
                        "component_class": key[4], "count": count}
                       for key, count in sorted(summary.items(), key=lambda item: (-item[1], str(item[0])))],
           "promotion_authorized": False}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(json.dumps(payload, indent=2))
unreal.SystemLibrary.quit_editor()
