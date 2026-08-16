"""Measure the actual v058 PR-006-to-PR-008 steel-strip handoff in world space."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR008ServoBlankingCandidate_v058"
AUDIT = PROJECT / "Saved/Audits/press_shop_pr006_pr008_strip_continuity_v058.json"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")


def bounds_payload(actor):
    origin, extent = actor.get_actor_bounds(False, False)
    return {
        "actor": actor.get_actor_label(),
        "origin_cm": [origin.x, origin.y, origin.z],
        "extent_cm": [extent.x, extent.y, extent.z],
        "min_cm": [origin.x - extent.x, origin.y - extent.y, origin.z - extent.z],
        "max_cm": [origin.x + extent.x, origin.y + extent.y, origin.z + extent.z],
    }


all_actors = actors.get_all_level_actors()
pr006_strip_actor = next(
    (actor for actor in all_actors if actor.get_actor_label() == "LB_PR006_V054_PR006_ThreadedStrip"), None
)
pr008_strip_actor = next(
    (actor for actor in all_actors if actor.get_actor_label() == "LB_PR008_V058_PR008_ThreadedStrip"), None
)
if pr006_strip_actor is None or pr008_strip_actor is None:
    raise RuntimeError(
        "Missing strip actors: "
        f"PR006={pr006_strip_actor is not None} PR008={pr008_strip_actor is not None}"
    )

pr006 = bounds_payload(pr006_strip_actor)
pr008 = bounds_payload(pr008_strip_actor)
gap_cm = pr008["min_cm"][0] - pr006["max_cm"][0]
vertical_delta_cm = pr008["origin_cm"][2] - pr006["origin_cm"][2]
lateral_delta_cm = pr008["origin_cm"][1] - pr006["origin_cm"][1]

# A continuous flat steel surface needs overlap or a deliberately modelled bridge.
continuous = gap_cm <= 1.0 and abs(vertical_delta_cm) <= 5.0 and abs(lateral_delta_cm) <= 1.0
payload = {
    "$schema": "line-boss/audit/press-shop-pr006-pr008-strip-continuity-v058/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": (
        "PR006_PR008_STRIP_CONTINUITY_PASS__NOT_PROMOTED"
        if continuous
        else "PR006_PR008_STRIP_BRIDGE_REQUIRED__NOT_PROMOTED"
    ),
    "map": MAP,
    "pr006_threaded_strip": pr006,
    "pr008_threaded_strip": pr008,
    "longitudinal_surface_gap_cm": gap_cm,
    "vertical_centre_delta_cm": vertical_delta_cm,
    "lateral_centre_delta_cm": lateral_delta_cm,
    "continuity_tolerance_cm": {
        "maximum_gap": 1.0,
        "maximum_vertical_centre_delta": 5.0,
        "maximum_lateral_centre_delta": 1.0,
    },
    "continuous": continuous,
    "decision": (
        "Existing strip meshes form a continuous handoff."
        if continuous
        else "Model a supported modular strip bridge from the PR-006 outfeed to the PR-008 loop-control entry; do not stretch either machine envelope."
    ),
    "promotion_authorized": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(
    "LINE_BOSS_PR006_PR008_STRIP_AUDIT "
    f"gap_cm={gap_cm:.3f} vertical_delta_cm={vertical_delta_cm:.3f} "
    f"lateral_delta_cm={lateral_delta_cm:.3f} continuous={continuous}"
)
unreal.SystemLibrary.quit_editor()
