"""Read-only AABB screening between restored PR009/10 blockers and train blockers."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
candidate = os.environ.get("LB_RESTORED_TRAIN_OVERLAP_CANDIDATE", "v239").lower()
MAP = f"/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_{candidate}"
OUT = ROOT / f"Saved/Audits/PressShopIntegration/press_shop_{candidate}_restored_train_collision_overlap.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)


def bounds(actor):
    origin, extent = actor.get_actor_bounds(False)
    return ([origin.x - extent.x, origin.y - extent.y, origin.z - extent.z],
            [origin.x + extent.x, origin.y + extent.y, origin.z + extent.z])


def blocking_record(actor):
    if not isinstance(actor, unreal.StaticMeshActor):
        return None
    component = actor.static_mesh_component
    if component.get_collision_enabled() == unreal.CollisionEnabled.NO_COLLISION:
        return None
    minimum, maximum = bounds(actor)
    return {"label": actor.get_actor_label(), "min": minimum, "max": maximum,
            "collision": str(component.get_collision_enabled()), "tags": [str(tag) for tag in actor.tags]}


restored = []
trains = []
for actor in actors_api.get_all_level_actors():
    tags = [str(tag) for tag in actor.tags]
    row = blocking_record(actor)
    if row is None:
        continue
    if "LB.Integration.WholeShop.RestoredAcceptedPresentation.v239" in tags:
        restored.append(row)
    train_tag = next((tag for tag in tags if tag.startswith("LB.PressTrain.Installed.TRAIN_")), None)
    if train_tag:
        row["train"] = train_tag.rsplit("_", 1)[-1]
        trains.append(row)

overlaps = []
for upstream in restored:
    for train in trains:
        depth = [min(upstream["max"][axis], train["max"][axis]) -
                 max(upstream["min"][axis], train["min"][axis]) for axis in range(3)]
        if min(depth) <= 5.0:
            continue
        overlaps.append({
            "restored_actor": upstream["label"],
            "train": train["train"],
            "train_actor": train["label"],
            "overlap_depth_cm": depth,
            "overlap_volume_cm3": depth[0] * depth[1] * depth[2],
        })
overlaps.sort(key=lambda row: row["overlap_volume_cm3"], reverse=True)
payload = {
    "$schema": "cairnwell/audit/press-shop-v239-restored-train-collision-overlap/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__NO_RESTORED_MACHINE_TO_TRAIN_BLOCKER_AABB_OVERLAPS" if not overlaps else "REVIEW__RESTORED_MACHINE_TO_TRAIN_BLOCKER_AABB_OVERLAPS_DETECTED",
    "map": MAP,
    "method": "conservative world-axis actor-bound screen; requires review before treating contacts as physical collisions",
    "minimum_overlap_depth_each_axis_cm": 5.0,
    "restored_blocker_count": len(restored),
    "train_blocker_count": len(trains),
    "overlap_pair_count": len(overlaps),
    "overlaps": overlaps,
    "read_only": True,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({key: payload[key] for key in (
    "status", "restored_blocker_count", "train_blocker_count", "overlap_pair_count")}, indent=2))
unreal.SystemLibrary.quit_editor()
