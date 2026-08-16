"""Read-only inventory of inbound-logistics actors in retained v438."""
from pathlib import Path
import json
import unreal

ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_inbound_binding_v482.json"

unreal.EditorLoadingAndSavingUtils.load_map(MAP)
actor_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
tokens = ("coilagv", "coil agv", "lorry", "truck", "inbound", "delivery", "crane", "coilslot", "pr003", "pr-003")
rows = []
class_counts = {}
for actor in actor_api.get_all_level_actors():
    label = actor.get_actor_label()
    tags = [str(tag) for tag in actor.tags]
    class_name = actor.get_class().get_name()
    search = (label + " " + class_name + " " + " ".join(tags)).lower()
    if not any(token in search for token in tokens):
        continue
    origin, extent = actor.get_actor_bounds(False)
    rows.append({
        "label": label,
        "class": class_name,
        "location_cm": list(actor.get_actor_location().to_tuple()),
        "bounds_origin_cm": list(origin.to_tuple()),
        "bounds_extent_cm": list(extent.to_tuple()),
        "tags": tags,
    })
    class_counts[class_name] = class_counts.get(class_name, 0) + 1

required_tags = (
    "LB.Vehicle.CoilAGV",
    "LB.Vehicle.CoilAGV.LiftDeck",
    "LB.Inventory.InTransfer",
)
payload = {
    "map": MAP,
    "map_saved": False,
    "matching_actor_count": len(rows),
    "class_counts": class_counts,
    "required_runtime_tag_counts": {
        tag: sum(tag in row["tags"] for row in rows) for tag in required_tags
    },
    "has_lorry_or_truck_presentation": any(
        ("lorry" in (row["label"] + " " + " ".join(row["tags"])).lower()
         or "truck" in (row["label"] + " " + " ".join(row["tags"])).lower())
        and "endtruck" not in row["label"].lower()
        and not any("crane" in tag.lower() for tag in row["tags"])
        for row in rows
    ),
    "actors": rows,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
unreal.log(f"INBOUND_BINDING_V482 {OUT} actors={len(rows)}")
unreal.SystemLibrary.quit_editor()
