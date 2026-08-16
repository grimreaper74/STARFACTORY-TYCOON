"""Apply selective component collision without changing shared mesh assets."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR010CollisionNavigationCandidate_v099"
OUT = ROOT / "Saved/Audits/PR010_CollisionNavigation/pr010_collision_configuration_v099.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP): raise RuntimeError(MAP)

fixed_roles = {
    "deck", "enclosure_structure", "enclosure_panel", "upper_fascia",
    "inspection_glazing", "lane_bed", "service_side", "fixed", "LB.PR010.Shuttle.FixedRailBed",
}
moving_roles = {
    "moving_infeed_shuttle", "moving_carrier_roller", "moving_stop_pin",
    "moving_reservation_gate", "moving_quality_spur", "identified_blank_stack",
    "carrier_position", "quality_hold_stack",
}
fixed = []
query = []
neutral = []
failures = []

for actor in actors_api.get_all_level_actors():
    actor_tags = {str(tag) for tag in actor.tags}
    if "LB.Station.PR010" not in actor_tags or isinstance(actor, (unreal.CameraActor, unreal.TextRenderActor, unreal.LBPR010Station)):
        continue
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    if component is None:
        continue
    if "LB.Asset.Candidate.v098" in actor_tags and not actor.get_actor_label().startswith("LB_PR010_V097_"):
        # Retain authored v098 detail collision decisions.
        enabled = component.get_collision_enabled()
        if enabled != unreal.CollisionEnabled.NO_COLLISION:
            fixed.append(actor.get_actor_label())
        else:
            neutral.append(actor.get_actor_label())
        continue
    if fixed_roles.intersection(actor_tags):
        component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
        component.set_collision_profile_name(unreal.Name("BlockAll"))
        component.set_editor_property("can_ever_affect_navigation", True)
        fixed.append(actor.get_actor_label())
    elif moving_roles.intersection(actor_tags):
        component.set_collision_enabled(unreal.CollisionEnabled.QUERY_ONLY)
        component.set_collision_profile_name(unreal.Name("OverlapAllDynamic"))
        component.set_editor_property("can_ever_affect_navigation", False)
        query.append(actor.get_actor_label())
    else:
        component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        component.set_collision_profile_name(unreal.Name("NoCollision"))
        component.set_editor_property("can_ever_affect_navigation", False)
        neutral.append(actor.get_actor_label())

if len(fixed) < 50: failures.append(f"too few fixed/detail blockers: {len(fixed)}")
if len(query) != 91: failures.append(f"expected 91 query-only moving/stack actors, found {len(query)}")
if not levels.save_current_level(): failures.append("could not save v099")

result = {
    "$schema": "cairnwell/audit/pr010-collision-configuration-v099/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PR010_V099_SELECTIVE_FIXED_AND_QUERY_COLLISION_CONFIGURED__RUNTIME_SWEEPS_AND_NAV_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__PR010_V099_COLLISION_CONFIGURATION__NOT_PROMOTED",
    "map": MAP,
    "fixed_or_detail_blocker_count": len(fixed),
    "query_only_moving_or_stack_count": len(query),
    "navigation_neutral_count": len(neutral),
    "fixed_or_detail_blockers": fixed,
    "query_only_moving_or_stack": query,
    "failures": failures,
    "promotion_authorized": False,
}
OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR010_V099_COLLISION {result['status']} {OUT}")
if failures: raise RuntimeError("; ".join(failures))
