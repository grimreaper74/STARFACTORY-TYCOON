"""Read-only inventory and spatial audit of the installed PR005-PR010 chain."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v236"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_pr005_pr010_installed_chain_v236.json"
STATIONS = ["PR005", "PR006", "PR007", "PR008", "PR009", "PR010"]

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)


def station_match(actor, station):
    label = actor.get_actor_label().upper().replace("-", "")
    tags = {str(tag).upper().replace("-", "") for tag in actor.tags}
    token = station.upper().replace("-", "")
    return token in label or any(token in tag for tag in tags)


def actor_record(actor):
    origin, extent = actor.get_actor_bounds(False)
    location = actor.get_actor_location()
    return {
        "label": actor.get_actor_label(),
        "class": actor.get_class().get_name(),
        "location_cm": [location.x, location.y, location.z],
        "bounds_min_cm": [origin.x - extent.x, origin.y - extent.y, origin.z - extent.z],
        "bounds_max_cm": [origin.x + extent.x, origin.y + extent.y, origin.z + extent.z],
        "tags": [str(tag) for tag in actor.tags],
    }


rows = {}
all_actors = actors_api.get_all_level_actors()
for station in STATIONS:
    matched = [actor_record(actor) for actor in all_actors if station_match(actor, station)]
    physical = [row for row in matched if row["class"] in {
        "StaticMeshActor", "SkeletalMeshActor", "TextRenderActor", "DecalActor"
    }]
    if physical:
        union_min = [min(row["bounds_min_cm"][axis] for row in physical) for axis in range(3)]
        union_max = [max(row["bounds_max_cm"][axis] for row in physical) for axis in range(3)]
    else:
        union_min = union_max = None
    rows[station] = {
        "matched_actor_count": len(matched),
        "physical_presentation_count": len(physical),
        "class_counts": {name: sum(row["class"] == name for row in matched)
                         for name in sorted({row["class"] for row in matched})},
        "presentation_union_min_cm": union_min,
        "presentation_union_max_cm": union_max,
        "actors": sorted(matched, key=lambda row: (row["class"], row["label"])),
    }

# Spatial gaps use the dominant east-west flow axis.  They are descriptive,
# not invented engineering clearances or placement authority.
gaps = []
for upstream, downstream in zip(STATIONS, STATIONS[1:]):
    up = rows[upstream]
    down = rows[downstream]
    gap = None
    if up["presentation_union_max_cm"] and down["presentation_union_min_cm"]:
        gap = down["presentation_union_min_cm"][0] - up["presentation_union_max_cm"][0]
    gaps.append({"upstream": upstream, "downstream": downstream, "x_gap_cm_descriptive": gap})

payload = {
    "$schema": "cairnwell/audit/press-shop-pr005-pr010-installed-chain-v236/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "READ_ONLY__NO_ASSETS_CHANGED",
    "map": MAP,
    "stations": rows,
    "descriptive_x_gaps": gaps,
    "placement_authority": "EXISTING_MAP_ONLY__NO_NEW_DATUMS_INVENTED",
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({
    "status": payload["status"],
    "counts": {key: {"matched": value["matched_actor_count"], "physical": value["physical_presentation_count"]}
               for key, value in rows.items()},
    "gaps": gaps,
}, indent=2))
unreal.SystemLibrary.quit_editor()
