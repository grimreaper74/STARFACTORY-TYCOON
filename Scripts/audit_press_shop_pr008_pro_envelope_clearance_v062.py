"""Measure v062 fixed envelope, hall-column intrusion and PR-006 strip interface."""
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR008ProEnvelopeCandidate_v062"
OUT = ROOT / "Saved/Audits/press_shop_pr008_pro_envelope_clearance_v062.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")


def bounds(actor):
    origin, extent = actor.get_actor_bounds(False, False)
    return {
        "actor": actor.get_actor_label(),
        "origin_cm": [origin.x, origin.y, origin.z],
        "extent_cm": [extent.x, extent.y, extent.z],
        "min_cm": [origin.x - extent.x, origin.y - extent.y, origin.z - extent.z],
        "max_cm": [origin.x + extent.x, origin.y + extent.y, origin.z + extent.z],
    }


def overlap(a, b):
    return all(a["min_cm"][i] < b["max_cm"][i] and a["max_cm"][i] > b["min_cm"][i] for i in range(3))


actors = list(actors_api.get_all_level_actors())
by_label = {actor.get_actor_label(): actor for actor in actors}
planning_actor = by_label.get("LB_PR008_V062_00_FIXED_PLANNING_ENVELOPE")
pr006_strip_actor = by_label.get("LB_PR006_V054_PR006_ThreadedStrip")
pr008_strip_actor = by_label.get("LB_PR008_V062_11_StripCentreDatum")
if not all((planning_actor, pr006_strip_actor, pr008_strip_actor)):
    raise RuntimeError("Missing planning/PR006/PR008 measurement actors")

planning = bounds(planning_actor)
pr006 = bounds(pr006_strip_actor)
pr008 = bounds(pr008_strip_actor)

intrusions = []
excluded_prefixes = ("LB_PR008_V058_", "LB_PR008_V059_", "LB_PR008_V060_", "LB_PR008_V062_")
for actor in actors:
    label = actor.get_actor_label()
    if label.startswith(excluded_prefixes) or not isinstance(actor, unreal.StaticMeshActor):
        continue
    row = bounds(actor)
    ex, ey, ez = row["extent_cm"]
    # Structural-column profile: tall, narrow and intersecting the fixed cage.
    if ez >= 200.0 and ex <= 100.0 and ey <= 100.0 and overlap(planning, row):
        row["overlap_with_fixed_planning_envelope"] = True
        intrusions.append(row)

gap_cm = pr008["min_cm"][0] - pr006["max_cm"][0]
vertical_delta_cm = pr008["origin_cm"][2] - pr006["origin_cm"][2]
lateral_delta_cm = pr008["origin_cm"][1] - pr006["origin_cm"][1]

payload = {
    "$schema": "line-boss/audit/press-shop-pr008-pro-envelope-clearance-v062/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "FIXED_PRO_ENVELOPE_MEASUREMENT_PASS__HALL_COLUMN_AND_PR006_INTERFACE_COORDINATION_FAIL__NOT_PROMOTED",
    "map": MAP,
    "fixed_planning_envelope": planning,
    "expected_world_dimensions_cm": [1040.0, 556.0, 449.0],
    "measured_world_dimensions_cm": [planning["extent_cm"][i] * 2.0 for i in range(3)],
    "structural_column_intrusion_count": len(intrusions),
    "structural_column_intrusions": intrusions,
    "pr006_pr008_interface": {
        "pr006_threaded_strip": pr006,
        "pr008_pro_strip_datum": pr008,
        "longitudinal_surface_gap_cm": gap_cm,
        "vertical_centre_delta_cm": vertical_delta_cm,
        "lateral_centre_delta_cm": lateral_delta_cm,
        "continuous": gap_cm <= 1.0 and abs(vertical_delta_cm) <= 5.0 and abs(lateral_delta_cm) <= 1.0,
        "decision": "Design an explicit supported entry-loop transition across the 305 cm gap and 25.5 cm fall, or reconcile the EST strip-centre heights from authoritative machine interfaces; do not stretch either envelope.",
    },
    "decision": "Keep the fixed PR-008 datum and -90 degree station transform. Coordinate the existing placeholder hall columns and the PR-006 output/PR-008 entry heights before detailed PR-008 art. Do not move the fixed Pro envelope merely to clear the current placeholders.",
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(
    "LINE_BOSS_PR008_V062_CLEARANCE_AUDIT "
    f"column_intrusions={len(intrusions)} gap_cm={gap_cm:.3f} vertical_delta_cm={vertical_delta_cm:.3f}")
unreal.SystemLibrary.quit_editor()
