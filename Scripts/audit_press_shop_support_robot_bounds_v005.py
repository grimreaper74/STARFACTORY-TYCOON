"""Report combined world bounds for each placed LB-CR01 unit."""
import json
from pathlib import Path
import unreal

MAP = "/Game/LineBoss/Maps/LB_PressShop_SupportRobotsCandidate_v005"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_lb_cr01_v005_world_bounds.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels.load_level(MAP)
report = {}
for unit in ("WEST", "EAST"):
    selected = [a for a in actors.get_all_level_actors() if a.get_actor_label().startswith(f"LB_CR01_{unit}_")]
    mins = unreal.Vector(1e12, 1e12, 1e12)
    maxs = unreal.Vector(-1e12, -1e12, -1e12)
    for actor in selected:
        origin, extent = actor.get_actor_bounds(False, False)
        mins.x = min(mins.x, origin.x - extent.x)
        mins.y = min(mins.y, origin.y - extent.y)
        mins.z = min(mins.z, origin.z - extent.z)
        maxs.x = max(maxs.x, origin.x + extent.x)
        maxs.y = max(maxs.y, origin.y + extent.y)
        maxs.z = max(maxs.z, origin.z + extent.z)
    report[unit] = {"actor_count": len(selected), "min_cm": [mins.x, mins.y, mins.z], "max_cm": [maxs.x, maxs.y, maxs.z]}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PRESS_V005_BOUNDS {report}")
