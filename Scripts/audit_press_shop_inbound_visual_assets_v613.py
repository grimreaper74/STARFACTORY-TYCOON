"""Read-only inventory of installed inbound presentation assets in exact v597."""

from pathlib import Path
import json
import unreal


MAP = "/Game/LineBoss/Developer/Validation/LB_PressShop_InboundReleaseCandidate_v597"
ROOT = Path(unreal.Paths.project_dir())
OUT = ROOT / "Saved/Audits/PressShopIntegration/inbound_visual_asset_inventory_v613.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)

rows = []
for actor in actors_api.get_all_level_actors():
    tags = {str(tag) for tag in actor.tags}
    label = actor.get_actor_label()
    if not (any(tag.startswith("LB.Inbound") for tag in tags) or label.startswith("LB_INBOUND")):
        continue
    row = {
        "class": actor.get_class().get_name(),
        "label": label,
        "tags": sorted(tags),
        "location_cm": list(actor.get_actor_location().to_tuple()),
        "rotation_deg": [actor.get_actor_rotation().pitch, actor.get_actor_rotation().yaw, actor.get_actor_rotation().roll],
    }
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    if component:
        mesh = component.get_editor_property("static_mesh")
        row["mesh"] = mesh.get_path_name() if mesh else None
        row["materials"] = [
            material.get_path_name() if material else None
            for material in component.get_materials()
        ]
    rows.append(row)

payload = {
    "status": "PASS__READ_ONLY",
    "map": MAP,
    "actor_count": len(rows),
    "actors": sorted(rows, key=lambda row: row["label"]),
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LB_INBOUND_VISUAL_ASSET_INVENTORY_V613::{json.dumps(payload)}")

