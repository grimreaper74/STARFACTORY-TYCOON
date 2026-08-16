"""Read-only support-area inventory for retained whole-shop map v249."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v249"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/PressShopIntegration/press_shop_support_area_inventory_v249.json"

# Authoritative EST-P world anchors from press_shop_master_plan_anchors_v001.json.
ANCHORS = {
    "PR-039_FIRST_OFF_SCAN": (9900.0, -4600.0, 0.0),
    "PR-040_QUARANTINE": (9900.0, -3200.0, 0.0),
    "PR-041_TRIM_SCRAP_BALER": (-8800.0, 4200.0, 0.0),
    "PR-042_DIE_SERVICES": (7800.0, -2000.0, 0.0),
    "PR-043_STILLAGE_MARSHALLING": (9900.0, -800.0, 0.0),
    "PR-044_DISPATCH_HANDOFF": (9900.0, 2000.0, 0.0),
    "CTRL_CONTROL_ROOM": (2200.0, 4500.0, 0.0),
    "QLAB_METROLOGY": (4100.0, 4500.0, 0.0),
    "MAINT_WORKSHOP": (-5800.0, 4500.0, 0.0),
    "UTIL_MONITORING": (-900.0, 4500.0, 0.0),
}

TOKENS = {
    "control_room": ("control", "console", "cctv", "operator", "playerstart"),
    "quality_metrology": ("quality", "inspect", "metrology", "scan", "quarantine"),
    "maintenance_tooling": ("maint", "tool", "die", "service", "workshop", "repair"),
    "utilities": ("util", "electrical", "cabinet", "power", "air", "hydraulic", "cooling", "network"),
    "logistics_dispatch": ("pallet", "stillage", "dispatch", "marshalling", "dock", "agv", "logistics"),
    "scrap_waste_fire": ("scrap", "baler", "waste", "fire", "extinguisher", "emergency"),
}


def vec(actor):
    p = actor.get_actor_location()
    return [round(float(p.x), 3), round(float(p.y), 3), round(float(p.z), 3)]


def distance_xy(location, anchor):
    dx = location[0] - anchor[0]
    dy = location[1] - anchor[1]
    return (dx * dx + dy * dy) ** 0.5


levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()

rows = []
all_actor_rows = []
for actor in actors:
    label = actor.get_actor_label()
    tags = [str(tag) for tag in actor.tags]
    haystack = (label + " " + " ".join(tags) + " " + actor.get_class().get_name()).lower()
    categories = [name for name, terms in TOKENS.items() if any(term in haystack for term in terms)]
    location = vec(actor)
    base_row = {
        "label": label,
        "class": actor.get_class().get_name(),
        "location_cm": location,
        "tags": tags,
    }
    all_actor_rows.append(base_row)
    if categories:
        nearest_name, nearest_anchor = min(
            ANCHORS.items(), key=lambda item: distance_xy(location, item[1]))
        rows.append({**base_row,
            "matched_categories": categories,
            "nearest_authoritative_anchor": nearest_name,
            "distance_to_anchor_xy_cm": round(distance_xy(location, nearest_anchor), 3),
        })

nearest = {}
for anchor_name, anchor in ANCHORS.items():
    ranked = sorted(all_actor_rows, key=lambda row: distance_xy(row["location_cm"], anchor))[:20]
    nearest[anchor_name] = [
        {**row, "distance_to_this_anchor_xy_cm": round(distance_xy(row["location_cm"], anchor), 3)}
        for row in ranked
    ]

counts = {name: sum(name in row["matched_categories"] for row in rows) for name in TOKENS}
payload = {
    "$schema": "cairnwell/audit/press-shop-support-area-inventory-v249/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "READ_ONLY_INVENTORY__NO_PLACEMENT_OR_PROMOTION_AUTHORIZED",
    "map": MAP,
    "actor_count": len(actors),
    "matched_actor_count": len(rows),
    "category_counts": counts,
    "authoritative_anchor_status": "EST-P; verify visually before art lock",
    "nearest_matches_by_anchor": nearest,
    "all_matches": sorted(rows, key=lambda row: row["label"]),
    "limitations": [
        "Name/tag matching proves inventory candidates, not semantic completeness.",
        "Generic shell actors are intentionally excluded unless named or tagged for support use.",
        "No new engineering placement, dimensions or authority are inferred by this audit.",
    ],
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LB_V249_SUPPORT_INVENTORY::{json.dumps({'actors': len(actors), 'matches': len(rows), 'counts': counts})}")
unreal.SystemLibrary.quit_editor()
