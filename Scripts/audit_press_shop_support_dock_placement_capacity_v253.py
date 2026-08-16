"""Read-only four-berth placement-capacity study for retained support layout v253."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v253"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/SupportRobots/press_shop_support_dock_placement_capacity_v253.json"
ROOT_Y_CM = 5160.0

# Authoritative support-bay extents from the v253 construction script.
BAYS = {
    "MR01_MAINT": {"centre_x": -5800.0, "width": 1900.0, "dock_type": "MR01", "required_berths": 2},
    "CR01_UTIL": {"centre_x": -900.0, "width": 1700.0, "dock_type": "CR01", "required_berths": 2},
}

# Conservative axis-aligned envelopes in world centimetres for a north-wall dock
# whose robot faces south. The dock source root is the docked robot centre.
LOCAL_VOLUMES = {
    "structure": {"min": [-130.0, 69.0, 0.0], "max": [130.0, 214.0, 171.0]},
    "side_service": {"min": [-230.0, 50.0, 0.0], "max": [230.0, 214.0, 220.0]},
    "straight_approach": {"min": [-70.0, -300.0, 0.0], "max": [70.0, 0.0, 220.0]},
}

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")


def actor_record(actor):
    if not isinstance(actor, unreal.StaticMeshActor):
        return None
    component = actor.static_mesh_component
    if component.get_collision_enabled() == unreal.CollisionEnabled.NO_COLLISION:
        return None
    origin, extent = actor.get_actor_bounds(False)
    label = actor.get_actor_label()
    ignored_tokens = ("floor", "roof", "ceiling", "liner", "bayfloor", "zone_")
    if any(token in label.lower() for token in ignored_tokens):
        return None
    return {
        "label": label,
        "tags": [str(tag) for tag in actor.tags],
        "min": [origin.x - extent.x, origin.y - extent.y, origin.z - extent.z],
        "max": [origin.x + extent.x, origin.y + extent.y, origin.z + extent.z],
    }


blockers = [row for row in (actor_record(actor) for actor in actors_api.get_all_level_actors()) if row]


def translated(volume, x, y):
    return {
        "min": [volume["min"][0] + x, volume["min"][1] + y, volume["min"][2]],
        "max": [volume["max"][0] + x, volume["max"][1] + y, volume["max"][2]],
    }


def collision_hits(bounds):
    hits = []
    for blocker in blockers:
        depth = [min(bounds["max"][axis], blocker["max"][axis]) -
                 max(bounds["min"][axis], blocker["min"][axis]) for axis in range(3)]
        if min(depth) > 5.0:
            hits.append({
                "actor": blocker["label"],
                "overlap_depth_cm": [round(value, 3) for value in depth],
            })
    return hits


def best_pair(valid_positions):
    pairs = []
    # Each root needs 230 cm half-width including side service. Two roots therefore
    # need at least 460 cm separation for non-overlapping service envelopes.
    for index, left in enumerate(valid_positions):
        for right in valid_positions[index + 1:]:
            separation = right["root_x_cm"] - left["root_x_cm"]
            if separation < 460.0:
                continue
            pairs.append({
                "root_x_cm": [left["root_x_cm"], right["root_x_cm"]],
                "root_y_cm": ROOT_Y_CM,
                "centre_balance_error_cm": abs((left["root_x_cm"] + right["root_x_cm"]) * 0.5),
                "separation_cm": separation,
            })
    return pairs


results = {}
for bay_id, bay in BAYS.items():
    bay_min = bay["centre_x"] - bay["width"] * 0.5
    bay_max = bay["centre_x"] + bay["width"] * 0.5
    root_min = bay_min + 230.0
    root_max = bay_max - 230.0
    trials = []
    x = root_min
    while x <= root_max + 0.01:
        volume_hits = {}
        for volume_name, volume in LOCAL_VOLUMES.items():
            volume_hits[volume_name] = collision_hits(translated(volume, x, ROOT_Y_CM))
        valid = not any(volume_hits.values())
        trials.append({
            "root_x_cm": round(x, 3),
            "root_y_cm": ROOT_Y_CM,
            "valid": valid,
            "hits": volume_hits,
        })
        x += 25.0
    valid_positions = [trial for trial in trials if trial["valid"]]
    pairs = best_pair(valid_positions)
    # Rank around the actual bay centre, then prefer wider separation.
    for pair in pairs:
        pair["centre_balance_error_cm"] = round(
            abs((sum(pair["root_x_cm"]) * 0.5) - bay["centre_x"]), 3
        )
    pairs.sort(key=lambda pair: (pair["centre_balance_error_cm"], -pair["separation_cm"]))
    results[bay_id] = {
        "dock_type": bay["dock_type"],
        "required_berths": bay["required_berths"],
        "bay_x_range_cm": [bay_min, bay_max],
        "root_x_scan_range_cm": [root_min, root_max],
        "root_y_cm": ROOT_Y_CM,
        "trial_count": len(trials),
        "valid_root_count": len(valid_positions),
        "valid_pair_count": len(pairs),
        "recommended_pair": pairs[0] if pairs else None,
        "valid_roots_cm": [trial["root_x_cm"] for trial in valid_positions],
        "trials": trials,
    }

all_capacity_pass = all(
    result["valid_pair_count"] > 0 and result["required_berths"] == 2
    for result in results.values()
)
payload = {
    "$schema": "cairnwell/audit/press-shop-support-dock-placement-capacity-v253/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__FOUR_COLLISION_FREE_BERTH_ENVELOPES_FOUND__PLACEMENT_STILL_TBC_NOT_INSTALLED" if all_capacity_pass
              else "FAIL__FOUR_BERTH_CAPACITY_NOT_PROVED",
    "map": MAP,
    "required_fleet": {"CR01": 2, "MR01": 2},
    "required_berths": {"CR01": 2, "MR01": 2},
    "dock_asset_strategy": "One reusable CR01 dock asset instanced twice and one reusable MR01 dock asset instanced twice.",
    "root_orientation": "Robot local +X faces world -Y; dock structure is north of each docked robot root.",
    "volumes_cm": LOCAL_VOLUMES,
    "blocker_count_screened": len(blockers),
    "results": results,
    "limitations": [
        "Read-only conservative AABB capacity study; no actor is placed or promoted.",
        "The v253 support anchors are EST-P and require fixed-camera visual review before art lock.",
        "CR01 wet-service routes, drainage and MR01 tool/consumable replenishment remain TBC.",
        "Final pair placement must repeat collision, navigation, door/drawer sweep, pedestrian route and runtime charging gates."
    ],
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({
    "status": payload["status"],
    "blocker_count_screened": len(blockers),
    "recommended_pairs": {key: value["recommended_pair"] for key, value in results.items()},
}, indent=2))
unreal.SystemLibrary.quit_editor()
