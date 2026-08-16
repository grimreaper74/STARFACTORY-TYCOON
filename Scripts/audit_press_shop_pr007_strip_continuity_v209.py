"""Measure inherited PR-007 strip and bridge continuity on exact v209."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR007ReleaseArtCandidate_v209"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_pr007_strip_continuity_v209.json"
LABELS = [
    "LB_PR007_V056_PR007_UpstreamStripBridge",
    "LB_PR007_V055_PR007_ThreadedStrip",
    "LB_PR007_V056_PR007_DownstreamStripBridge",
]

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"could not load {MAP}")

by_label = {actor.get_actor_label(): actor for actor in actors_api.get_all_level_actors()}
rows = []
failures = []
for label in LABELS:
    actor = by_label.get(label)
    if actor is None:
        failures.append(f"missing {label}")
        continue
    origin, extent = actor.get_actor_bounds(False, False)
    rows.append({
        "actor": label,
        "origin_cm": [origin.x, origin.y, origin.z],
        "extent_cm": [extent.x, extent.y, extent.z],
        "min_x_cm": origin.x - extent.x,
        "max_x_cm": origin.x + extent.x,
        "min_z_cm": origin.z - extent.z,
        "max_z_cm": origin.z + extent.z,
        "centre_y_cm": origin.y,
        "centre_z_cm": origin.z,
    })

rows.sort(key=lambda row: row["min_x_cm"])
joints = []
for left, right in zip(rows, rows[1:]):
    gap = right["min_x_cm"] - left["max_x_cm"]
    lateral = right["centre_y_cm"] - left["centre_y_cm"]
    # The upstream bridge is a shallow ramp, so centre-to-centre height is not
    # a valid continuity measure.  Gate the actual world-space Z intervals.
    vertical = max(
        0.0,
        right["min_z_cm"] - left["max_z_cm"],
        left["min_z_cm"] - right["max_z_cm"],
    )
    passed = gap <= 1.0 and abs(lateral) <= 1.0 and vertical <= 1.0
    joints.append({
        "left": left["actor"],
        "right": right["actor"],
        "longitudinal_gap_cm": gap,
        "lateral_centre_error_cm": lateral,
        "vertical_surface_interval_gap_cm": vertical,
        "pass": passed,
    })
    if not passed:
        failures.append(f"discontinuous joint {left['actor']} -> {right['actor']}")

if len(rows) != len(LABELS) or len(joints) != 2:
    failures.append("strip/bridge inventory incomplete")

payload = {
    "$schema": "cairnwell/audit/press-shop-pr007-strip-continuity-v209/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": ("PR007_INHERITED_STRIP_BRIDGE_CONTINUITY_PASS__NOT_PROMOTED"
               if not failures else "PR007_STRIP_BRIDGE_CONTINUITY_FAIL__NOT_PROMOTED"),
    "map": MAP,
    "segments": rows,
    "joints": joints,
    "tolerance_cm": {"maximum_longitudinal_gap": 1.0, "lateral_centre": 1.0, "vertical_surface_interval_gap": 1.0},
    "release_detail_changed_strip_or_bridges": False,
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
unreal.SystemLibrary.quit_editor()
