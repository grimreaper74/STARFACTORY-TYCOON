"""Read actual world bounds of the candidate's existing outbound automation assets."""

import json
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_outbound_bounds_v026.json"
LABELS = ("MESHY | S06 Vision / outfeed | reused press asset", "ROBOT | S06 | vision stack robot", "OUTBOUND | real vision inspection gate", "OUTBOUND | inspected panel stillage")

if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load candidate")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
rows = {}
for label in LABELS:
    actor = actors.get(label)
    if actor is None:
        raise RuntimeError("Required actor missing: " + label)
    origin, extent = actor.get_actor_bounds(False)
    rows[label] = {
        "origin_cm": [round(origin.x, 1), round(origin.y, 1), round(origin.z, 1)],
        "extent_cm": [round(extent.x, 1), round(extent.y, 1), round(extent.z, 1)],
        "min_cm": [round(origin.x - extent.x, 1), round(origin.y - extent.y, 1), round(origin.z - extent.z, 1)],
        "max_cm": [round(origin.x + extent.x, 1), round(origin.y + extent.y, 1), round(origin.z + extent.z, 1)],
    }
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({"status": "PASS__READ_ONLY_OUTBOUND_WORLD_BOUNDS", "actors": rows}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_OUTBOUND_BOUNDS_V026_PASS")
