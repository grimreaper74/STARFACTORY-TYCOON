"""Read-only inventory of existing automation actors in the 2126 candidate."""

import json
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_automation_candidates_v021.json"
TERMS = ("robot", "agv", "drone", "hover", "vision", "inspect", "transfer", "automation", "vacuum")


def visible(actor):
    components = actor.get_components_by_class(unreal.PrimitiveComponent)
    return bool(components) and all(component.is_visible() for component in components)


if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load candidate")
rows = []
for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    label = actor.get_actor_label()
    if not any(term in label.lower() for term in TERMS):
        continue
    loc = actor.get_actor_location()
    rows.append({
        "label": label,
        "class": actor.get_class().get_name(),
        "visible": visible(actor),
        "location_cm": [round(loc.x, 1), round(loc.y, 1), round(loc.z, 1)],
        "tags": [str(tag) for tag in actor.tags],
    })
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({"status": "PASS__READ_ONLY_AUTOMATION_INVENTORY", "actors": rows}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_AUTOMATION_CANDIDATES_V021_PASS")
