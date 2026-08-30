"""Read-only actor-slot audit for the individual-sprite candidate map."""
import json
from pathlib import Path

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShopFactorio2p5D_Full_v006_TopdownSprite/Maps/LB_PressShop_Factorio2p5D_Full_v006_TopdownSprite"
OUT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_sprite_proxy_slots_v001.json"

if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("PRESSSHOP_SPRITE_SLOT_AUDIT_FAIL: could not load candidate map")

records = []
for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    label = actor.get_actor_label()
    if "2.5D" not in label and "draw / form" not in label:
        continue
    location = actor.get_actor_location()
    rotation = actor.get_actor_rotation()
    record = {
        "label": label,
        "class": actor.get_class().get_name(),
        "location_cm": [round(location.x, 3), round(location.y, 3), round(location.z, 3)],
        "rotation": [round(rotation.pitch, 3), round(rotation.yaw, 3), round(rotation.roll, 3)],
    }
    if isinstance(actor, unreal.StaticMeshActor):
        scale = actor.get_actor_scale3d()
        record["scale"] = [round(scale.x, 3), round(scale.y, 3), round(scale.z, 3)]
        record["mesh"] = actor.static_mesh_component.static_mesh.get_path_name() if actor.static_mesh_component.static_mesh else None
    records.append(record)
records.sort(key=lambda value: value["label"].lower())
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"status": "PASS__READ_ONLY_SLOT_AUDIT", "map": MAP, "actors": records}, indent=2) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_SPRITE_SLOT_AUDIT_PASS=" + json.dumps(records, sort_keys=True))
