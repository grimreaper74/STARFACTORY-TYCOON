"""Author local PR-009 navigation coverage and exclude its protected process space."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from press_shop_pr009_in_map_validation_config import TARGET_MAP


ROOT = Path(unreal.Paths.project_dir())
OUT = ROOT / "Saved" / "Audits" / "PR009_InMap_v084" / "navigation_coverage_repair.json"
BOUNDS_LABEL = "LB_PR009_V084_NavBounds_LocalCoverage"
EXCLUSION_LABEL = "LB_PR009_V084_NavModifier_ProtectedProcessSpace"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(TARGET_MAP):
    raise RuntimeError(f"Could not load {TARGET_MAP}")

for actor in list(actors.get_all_level_actors()):
    if actor.get_actor_label() in {BOUNDS_LABEL, EXCLUSION_LABEL}:
        actors.destroy_actor(actor)

# The inherited PR-004 bounds end near world X=-3950 cm. PR-009 occupies
# X=220..980, Y=-2260..-1740. This local volume covers both validation routes
# and a service-access perimeter without changing visible/colliding geometry.
bounds = actors.spawn_actor_from_class(
    unreal.NavMeshBoundsVolume,
    unreal.Vector(600.0, -2000.0, 350.0),
    unreal.Rotator(),
)
if bounds is None:
    raise RuntimeError("Could not spawn PR-009 navigation bounds")
bounds.set_actor_label(BOUNDS_LABEL)
bounds.tags = [unreal.Name(value) for value in (
    "LB.Asset.Candidate.v084",
    "LB.Asset.CandidateNotPromoted",
    "LB.PR009.Navigation",
    "LB.Navigation.LocalCoverage",
)]
# Default volume brush is 200 cm on each axis: 18 x 16 x 7 m.
bounds.set_actor_scale3d(unreal.Vector(9.0, 8.0, 3.5))

# Explicitly remove navigation from the full guarded process envelope. This is
# stronger evidence than relying on guard collision alone and remains invisible.
exclusion = actors.spawn_actor_from_class(
    unreal.NavModifierVolume,
    unreal.Vector(600.0, -2000.0, 250.0),
    unreal.Rotator(),
)
if exclusion is None:
    raise RuntimeError("Could not spawn PR-009 protected-space nav modifier")
exclusion.set_actor_label(EXCLUSION_LABEL)
exclusion.tags = [unreal.Name(value) for value in (
    "LB.Asset.Candidate.v084",
    "LB.Asset.CandidateNotPromoted",
    "LB.PR009.Navigation",
    "LB.Navigation.ProtectedProcessSpace",
)]
# 8.0 x 6.0 x 5.0 m; intentionally covers the validator's protected rectangle
# X=240..960, Y=-2240..-1760 with a modest guard-line safety margin.
exclusion.set_actor_scale3d(unreal.Vector(4.0, 3.0, 2.5))
null_area = unreal.load_class(None, "/Script/NavigationSystem.NavArea_Null")
if null_area is None:
    raise RuntimeError("Could not load NavArea_Null")
exclusion.set_editor_property("area_class", null_area)

world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "RebuildNavigation")
for actor in actors.get_all_level_actors():
    if isinstance(actor, unreal.RecastNavMesh):
        actor.set_editor_property("runtime_generation", unreal.RuntimeGenerationType.DYNAMIC)
        actor.set_editor_property("can_be_main_nav_data", True)

if not levels.save_current_level():
    raise RuntimeError(f"Could not save {TARGET_MAP}")

def bounds_row(actor):
    origin, extent = actor.get_actor_bounds(False, False)
    return {
        "label": actor.get_actor_label(),
        "origin_cm": [origin.x, origin.y, origin.z],
        "size_cm": [extent.x * 2.0, extent.y * 2.0, extent.z * 2.0],
        "scale": [actor.get_actor_scale3d().x, actor.get_actor_scale3d().y, actor.get_actor_scale3d().z],
    }

payload = {
    "$schema": "cairnwell/audit/press-shop-pr009-navigation-coverage-repair/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__NAV_COVERAGE_AND_PROTECTED_EXCLUSION_AUTHORED__NOT_PROMOTED",
    "target_map": TARGET_MAP,
    "bounds": bounds_row(bounds),
    "protected_exclusion": bounds_row(exclusion),
    "area_class": null_area.get_path_name(),
    "visible_actor_changes": 0,
    "station_geometry_changes": 0,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
unreal.log(f"CAIRNWELL_PR009_NAV_COVERAGE_REPAIR_PASS output={OUT}")
unreal.SystemLibrary.quit_editor()
