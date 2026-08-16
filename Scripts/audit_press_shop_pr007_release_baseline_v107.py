"""Record exact PR-007 authority, mover attachments and visual context in v107."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_IntegratedEnvironmentCandidate_v107"
OUT = (Path(unreal.Paths.project_saved_dir()) /
       "Audits/PressShopIntegration/press_shop_pr007_release_baseline_v107.json")
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
    if isinstance(actor, unreal.SpotLight):
        component = actor.spot_light_component
        row["light"] = {
            "intensity": float(component.get_editor_property("intensity")),
            "attenuation_radius_cm": float(component.get_editor_property("attenuation_radius")),
            "inner_cone_deg": float(component.get_editor_property("inner_cone_angle")),
            "outer_cone_deg": float(component.get_editor_property("outer_cone_angle")),
        }
    return row


all_actors = actors_api.get_all_level_actors()
scope = [actor_row(actor) for actor in all_actors if "PR007" in actor.get_actor_label().upper()]
nearby = []
for actor in all_actors:
    location = actor.get_actor_location()
    if -3350 <= location.x <= -2150 and -2550 <= location.y <= -1450:
        if "PR007" not in actor.get_actor_label().upper():
            nearby.append(actor_row(actor))

expected = {
    "LB_PR007_V055_PR007_HoodWash": "PR007_WashHoodMover",
    "LB_PR007_V055_PR007_WashPumpMotor": "PR007_WashPumpMover",
    "LB_PR007_V055_PR007_LubePumpMotor": "PR007_LubePumpMover",
    "LB_PR007_V055_PR007_InfeedRollLower": "PR007_FeedRollerMover",
    "LB_PR007_V055_PR007_WashRollLower": "PR007_WashRollerMover",
    "LB_PR007_V055_PR007_LubeRollLower": "PR007_LubeRollerMover",
    "LB_PR007_V055_PR007_OutfeedRollLower": "PR007_OutfeedRollerMover",
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
failures = [row for row in bindings if row["actual_parent"] != row["expected_parent"]]
stations = [actor for actor in all_actors if isinstance(actor, unreal.LBPR007Station)]

payload = {
    "$schema": "cairnwell/audit/press-shop-pr007-release-baseline-v107/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": ("EXACT_V107_PR007_BASELINE_PASS__RELEASE_DETAIL_REQUIRED__NOT_PROMOTED"
               if len(stations) == 1 and not failures else "EXACT_V107_PR007_BASELINE_FAIL__NOT_PROMOTED"),
    "map": MAP,
    "approved_datum_cm": [-2700, -2000, 0],
    "pr007_actor_count": len(scope),
    "pr007_authority_count": len(stations),
    "binding_count": len(bindings),
    "binding_failure_count": len(failures),
    "bindings": bindings,
    "pr007_actors": sorted(scope, key=lambda row: row["label"]),
    "nearby_context": sorted(nearby, key=lambda row: row["label"]),
    "visual_holds": [
        "clean box-like casing lacks release fabricated depth",
        "wash spray, lubricant film and mist extraction are not visibly communicated",
        "filters, gauges, drains, service connections and maintenance logic are sparse",
        "materials are clean and uniform",
        "whole-hall context remains dark and sparse",
    ],
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR007_V107_BASELINE_{'PASS' if not failures else 'FAIL'} actors={len(scope)} bindings={len(bindings)}")
unreal.SystemLibrary.quit_editor()
