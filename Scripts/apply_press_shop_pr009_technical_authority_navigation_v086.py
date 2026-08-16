"""Consolidate PR-009 v086 flow authority and author invisible navigation coverage."""
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR009LayeredPresentationCandidate_v086"
PREFIX = "LB_PR009_V086_"
OUT = ROOT / "Saved/Audits/press_shop_pr009_technical_authority_navigation_v086.json"
SUITE_OUT = ROOT / "Saved/Audits/PR009_InMap_v086/navigation_coverage_repair.json"
BOUNDS_LABEL = PREFIX + "NavBounds_LocalCoverage"
EXCLUSION_LABEL = PREFIX + "NavModifier_ProtectedProcessSpace"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

actors = list(actors_api.get_all_level_actors())
pr008 = [actor for actor in actors if isinstance(actor, unreal.LBPR008Station)]
pr009 = [actor for actor in actors if isinstance(actor, unreal.LBPR009Station)]
flows = [actor for actor in actors if isinstance(actor, unreal.LBPressShopMaterialFlowController)]
if len(pr008) != 1 or len(pr009) != 1 or len(flows) not in (1, 2):
    raise RuntimeError(f"Authority precondition failed: PR008={len(pr008)} PR009={len(pr009)} flow={len(flows)}")

retained = next((actor for actor in flows if "PR004_PR005" in actor.get_actor_label()), flows[0])
destroyed = []
for actor in flows:
    if actor != retained:
        destroyed.append(actor.get_actor_label())
        actors_api.destroy_actor(actor)
retained.bind_blank_stations(pr008[0], pr009[0])
tags = [str(tag) for tag in retained.tags]
tags.extend(("LB.Traceability.PR008.PR009", "LB.Asset.Candidate.v086", "LB.Asset.CandidateNotPromoted"))
retained.tags = [unreal.Name(tag) for tag in dict.fromkeys(tags)]

for actor in list(actors_api.get_all_level_actors()):
    if actor.get_actor_label() in {BOUNDS_LABEL, EXCLUSION_LABEL}:
        actors_api.destroy_actor(actor)

bounds = actors_api.spawn_actor_from_class(
    unreal.NavMeshBoundsVolume, unreal.Vector(600.0, -2000.0, 350.0), unreal.Rotator())
if bounds is None:
    raise RuntimeError("Could not spawn PR-009 v086 navigation bounds")
bounds.set_actor_label(BOUNDS_LABEL)
bounds.tags = [unreal.Name(tag) for tag in (
    "LB.Asset.Candidate.v086", "LB.Asset.CandidateNotPromoted",
    "LB.PR009.Navigation", "LB.Navigation.LocalCoverage")]
bounds.set_actor_scale3d(unreal.Vector(9.0, 8.0, 3.5))

exclusion = actors_api.spawn_actor_from_class(
    unreal.NavModifierVolume, unreal.Vector(600.0, -2000.0, 250.0), unreal.Rotator())
if exclusion is None:
    raise RuntimeError("Could not spawn PR-009 v086 protected-space exclusion")
exclusion.set_actor_label(EXCLUSION_LABEL)
exclusion.tags = [unreal.Name(tag) for tag in (
    "LB.Asset.Candidate.v086", "LB.Asset.CandidateNotPromoted",
    "LB.PR009.Navigation", "LB.Navigation.ProtectedProcessSpace")]
exclusion.set_actor_scale3d(unreal.Vector(4.0, 3.0, 2.5))
null_area = unreal.load_class(None, "/Script/NavigationSystem.NavArea_Null")
if null_area is None:
    raise RuntimeError("Could not load NavArea_Null")
exclusion.set_editor_property("area_class", null_area)

world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "RebuildNavigation")
for actor in actors_api.get_all_level_actors():
    if isinstance(actor, unreal.RecastNavMesh):
        actor.set_editor_property("runtime_generation", unreal.RuntimeGenerationType.DYNAMIC)
        actor.set_editor_property("can_be_main_nav_data", True)

if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")

remaining_flows = [actor for actor in actors_api.get_all_level_actors()
                   if isinstance(actor, unreal.LBPressShopMaterialFlowController)]
payload = {
    "$schema": "cairnwell/audit/press-shop-pr009-technical-authority-navigation-v086/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": (
        "PR009_V086_SINGLETON_MATERIAL_FLOW_AND_NAVIGATION_PROTECTED_SPACE_AUTHORING_PASS__"
        "FULL_RUNTIME_SUITE_REQUIRED__NOT_PROMOTED"
        if len(remaining_flows) == 1 else "PR009_V086_TECHNICAL_AUTHORING_FAIL__NOT_PROMOTED"),
    "map": MAP,
    "pr008_authority": pr008[0].get_actor_label(),
    "pr009_authority": pr009[0].get_actor_label(),
    "retained_flow_controller": retained.get_actor_label(),
    "destroyed_duplicate_controllers": destroyed,
    "flow_controller_count_after": len(remaining_flows),
    "navigation_bounds": BOUNDS_LABEL,
    "protected_process_exclusion": EXCLUSION_LABEL,
    "protected_area_class": null_area.get_path_name(),
    "visible_actor_changes": 0,
    "station_geometry_changes": 0,
    "pr010_started": False,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
suite_payload = {
    "$schema": "cairnwell/audit/press-shop-pr009-navigation-coverage-repair/v1",
    "generated_utc": payload["generated_utc"],
    "status": "PASS__NAV_COVERAGE_AND_PROTECTED_EXCLUSION_AUTHORED__NOT_PROMOTED",
    "target_map": MAP,
    "bounds": {"label": BOUNDS_LABEL, "origin_cm": [600.0, -2000.0, 350.0],
               "size_cm": [1800.0, 1600.0, 700.0], "scale": [9.0, 8.0, 3.5]},
    "protected_exclusion": {"label": EXCLUSION_LABEL, "origin_cm": [600.0, -2000.0, 250.0],
                            "size_cm": [800.0, 600.0, 500.0], "scale": [4.0, 3.0, 2.5]},
    "area_class": null_area.get_path_name(),
    "source_authoring_audit": "Saved/Audits/press_shop_pr009_technical_authority_navigation_v086.json",
    "visible_actor_changes": 0,
    "station_geometry_changes": 0,
    "promotion_authorized": False,
}
SUITE_OUT.parent.mkdir(parents=True, exist_ok=True)
SUITE_OUT.write_text(json.dumps(suite_payload, indent=2) + "\n", encoding="utf-8")
unreal.log(payload["status"])
unreal.SystemLibrary.quit_editor()
if len(remaining_flows) != 1:
    raise RuntimeError("PR-009 v086 material-flow authority is not a singleton")
