"""Extend runtime robot navigation over PR-010 and exclude its process volume."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR010CollisionNavigationCandidate_v099"
OUT = ROOT / "Saved/Audits/PR010_CollisionNavigation/navigation_authoring_v099.json"
BOUNDS_LABEL = "LB_PR010_V099_NavBounds_LocalCoverage"
EXCLUSION_LABEL = "LB_PR010_V099_NavModifier_ProtectedProcessSpace"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP): raise RuntimeError(MAP)
for actor in list(actors.get_all_level_actors()):
    if actor.get_actor_label() in {BOUNDS_LABEL, EXCLUSION_LABEL}: actors.destroy_actor(actor)

bounds = actors.spawn_actor_from_class(unreal.NavMeshBoundsVolume, unreal.Vector(1360, -2000, 350), unreal.Rotator())
if bounds is None: raise RuntimeError("Could not spawn PR-010 navigation bounds")
bounds.set_actor_label(BOUNDS_LABEL)
bounds.tags = [unreal.Name(value) for value in ("LB.Asset.Candidate.v099", "LB.Asset.CandidateNotPromoted", "LB.PR010.Navigation", "LB.Navigation.LocalCoverage")]
bounds.set_actor_scale3d(unreal.Vector(7.0, 11.5, 3.5))

exclusion = actors.spawn_actor_from_class(unreal.NavModifierVolume, unreal.Vector(1350, -2000, 250), unreal.Rotator())
if exclusion is None: raise RuntimeError("Could not spawn PR-010 navigation exclusion")
exclusion.set_actor_label(EXCLUSION_LABEL)
exclusion.tags = [unreal.Name(value) for value in ("LB.Asset.Candidate.v099", "LB.Asset.CandidateNotPromoted", "LB.PR010.Navigation", "LB.Navigation.ProtectedProcessSpace")]
exclusion.set_actor_scale3d(unreal.Vector(4.2, 7.0, 2.5))
null_area = unreal.load_class(None, "/Script/NavigationSystem.NavArea_Null")
if null_area is None: raise RuntimeError("Could not load NavArea_Null")
exclusion.set_editor_property("area_class", null_area)

world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "RebuildNavigation")
for actor in actors.get_all_level_actors():
    if isinstance(actor, unreal.RecastNavMesh):
        actor.set_editor_property("runtime_generation", unreal.RuntimeGenerationType.DYNAMIC)
        actor.set_editor_property("can_be_main_nav_data", True)
if not levels.save_current_level(): raise RuntimeError("Could not save v099 navigation")

def row(actor):
    origin, extent = actor.get_actor_bounds(False, False)
    return {"label": actor.get_actor_label(), "origin_cm": [origin.x, origin.y, origin.z], "size_cm": [extent.x*2, extent.y*2, extent.z*2]}

payload = {
    "$schema": "cairnwell/audit/pr010-navigation-authoring-v099/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PR010_V099_NAV_COVERAGE_AND_PROTECTED_EXCLUSION_AUTHORED__PIE_GATE_REQUIRED__NOT_PROMOTED",
    "map": MAP, "bounds": row(bounds), "protected_exclusion": row(exclusion), "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
