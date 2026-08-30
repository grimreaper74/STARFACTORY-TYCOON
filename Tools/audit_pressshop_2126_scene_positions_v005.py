"""Read-only spatial audit for the fresh 2126 Press Shop candidate."""

import json
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
REPORT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Saved\Audits\PressShopIntegration\pressshop_2126_scene_positions_v005.json")
TERMS = ("coil", "meshy", "facade", "press", "steam", "fixture", "rail", "open bay")


if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load fresh candidate map")

rows = []
for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    label = actor.get_actor_label()
    bounds_origin, bounds_extent = actor.get_actor_bounds(False)
    location = actor.get_actor_location()
    named_interest = any(term in label.lower() for term in TERMS)
    large_near_candidate = (
        -25000.0 <= bounds_origin.x <= 6000.0
        and max(bounds_extent.x, bounds_extent.y, bounds_extent.z) >= 500.0
    )
    if not named_interest and not large_near_candidate:
        continue
    rows.append({
        "label": label,
        "class": actor.get_class().get_name(),
        "location_cm": [round(location.x, 1), round(location.y, 1), round(location.z, 1)],
        "bounds_origin_cm": [round(bounds_origin.x, 1), round(bounds_origin.y, 1), round(bounds_origin.z, 1)],
        "bounds_extent_cm": [round(bounds_extent.x, 1), round(bounds_extent.y, 1), round(bounds_extent.z, 1)],
    })

rows.sort(key=lambda row: row["label"].lower())
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({"status": "PASS__READ_ONLY", "map": MAP, "actors": rows}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_SCENE_POSITION_AUDIT_V005_PASS: %d rows" % len(rows))
