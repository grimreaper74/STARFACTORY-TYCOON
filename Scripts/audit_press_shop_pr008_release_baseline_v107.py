"""Record exact PR-008 authority, mover attachments and visual context in v107."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_IntegratedEnvironmentCandidate_v107"
OUT = (Path(unreal.Paths.project_saved_dir()) /
       "Audits/PressShopIntegration/press_shop_pr008_release_baseline_v107.json")
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)


def vec(value):
    return [round(float(value.x), 6), round(float(value.y), 6), round(float(value.z), 6)]


def actor_row(actor):
    row = {
        "label": actor.get_actor_label(),
        "class": actor.get_class().get_name(),
        "location_cm": vec(actor.get_actor_location()),
        "tags": sorted(str(tag) for tag in actor.tags),
    }
    if isinstance(actor, unreal.Light):
        component = actor.get_component_by_class(unreal.LightComponent)
        if component:
            row["light"] = {
                "intensity": float(component.get_editor_property("intensity")),
                "attenuation_radius_cm": float(component.get_editor_property("attenuation_radius")),
            }
    return row


all_actors = actors_api.get_all_level_actors()
scope_actors = [actor for actor in all_actors if "PR008" in actor.get_actor_label().upper()]
scope = [actor_row(actor) for actor in scope_actors]
nearby = []
for actor in all_actors:
    location = actor.get_actor_location()
    if -2200 <= location.x <= 100 and -2600 <= location.y <= -1400:
        if "PR008" not in actor.get_actor_label().upper():
            nearby.append(actor_row(actor))

expected = {
    "LB_PR008_V066_SM_CA_MW_PR008_ServoFeedRoll_Lower_01": "PR008_FeedRollLowerMover",
    "LB_PR008_V066_SM_CA_MW_PR008_ServoFeedSleeve_Lower_01": "PR008_FeedRollLowerMover",
    "LB_PR008_V066_SM_CA_MW_PR008_ServoFeedRoll_Upper_01": "PR008_FeedRollUpperMover",
    "LB_PR008_V066_SM_CA_MW_PR008_ServoFeedSleeve_Upper_01": "PR008_FeedRollUpperMover",
    "LB_PR008_V065_SM_CA_MW_PR008_EdgeGuide_Operator": "PR008_EdgeGuideOperatorMover",
    "LB_PR008_V065_SM_CA_MW_PR008_EdgeGuide_Drive": "PR008_EdgeGuideDriveMover",
    "LB_PR008_V067_SM_CA_MW_PR008_TelescopeStage1_01": "PR008_TelescopeStage1Mover",
    "LB_PR008_V067_SM_CA_MW_PR008_TelescopeStage2_01": "PR008_TelescopeStage2Mover",
    "LB_PR008_V067_SM_CA_MW_PR008_TelescopeStage3_01": "PR008_TelescopeStage3Mover",
    "LB_PR008_V068_SM_CA_MW_PR008_PrePunchSlide_01": "PR008_PrePunchMover",
    "LB_PR008_V068_SM_CA_MW_PR008_PrePunchScrapFlap_01": "PR008_ScrapFlapMover",
    "LB_PR008_V068_SM_CA_MW_PR008_PrePunchServiceDoor_Operator": "PR008_ServiceDoorOperatorMover",
    "LB_PR008_V068_SM_CA_MW_PR008_PrePunchServiceDoor_Drive": "PR008_ServiceDoorDriveMover",
    "LB_PR008_V069_SM_CA_MW_PR008_ShearBladeBeam_01": "PR008_GuillotineMover",
}
by_label = {actor.get_actor_label(): actor for actor in all_actors}
bindings = []
for label, expected_parent in expected.items():
    actor = by_label.get(label)
    root = actor.static_mesh_component if isinstance(actor, unreal.StaticMeshActor) else None
    parent = root.get_attach_parent() if root else None
    bindings.append({
        "actor": label,
        "expected_parent": expected_parent,
        "actual_parent": parent.get_name() if parent else None,
    })
binding_failures = [row for row in bindings if row["actual_parent"] != row["expected_parent"]]
stations = [actor for actor in all_actors if isinstance(actor, unreal.LBPR008Station)]
anchor_tabs = [actor.get_actor_label() for actor in scope_actors
               if "ANCHOR" in actor.get_actor_label().upper() or "BASEPLATE" in actor.get_actor_label().upper()]
source_versions = sorted({tag for actor in scope_actors for tag in (str(value) for value in actor.tags)
                          if "Candidate.v" in tag})

payload = {
    "$schema": "cairnwell/audit/press-shop-pr008-release-baseline-v107/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": ("EXACT_V107_PR008_BASELINE_PASS__RELEASE_DETAIL_AUDIT_COMPLETE__NOT_PROMOTED"
               if len(stations) == 1 and not binding_failures else "EXACT_V107_PR008_BASELINE_FAIL__NOT_PROMOTED"),
    "map": MAP,
    "pr008_actor_count": len(scope),
    "pr008_authority_count": len(stations),
    "binding_count": len(bindings),
    "binding_failure_count": len(binding_failures),
    "bindings": bindings,
    "candidate_tags_present": source_versions,
    "anchor_or_baseplate_actor_count": len(anchor_tabs),
    "anchor_or_baseplate_actors": sorted(anchor_tabs),
    "pr008_actors": sorted(scope, key=lambda row: row["label"]),
    "nearby_context": sorted(nearby, key=lambda row: row["label"]),
    "known_retained_v082_holds": [
        "generic external plates and studs should become authored base geometry",
        "hall context and mechanical/service density remain below release target",
        "distant Cairnwell/Moorcross identity is weak",
        "whole-hall context remains dark and sparse",
    ],
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR008_V107_BASELINE_{'PASS' if not binding_failures else 'FAIL'} actors={len(scope)} bindings={len(bindings)}")
unreal.SystemLibrary.quit_editor()
