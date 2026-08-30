"""Read-only placement audit for the v002 inbound composition."""
import json
from pathlib import Path

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v002/Maps/LB_PressShop_2126_Steam_v002"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_v002_inbound_composition_v022.json"

if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load candidate map")

needles = ("coil", "feeder", "process island", "factory deck", "infeed", "drawform")
rows = []
for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    label = actor.get_actor_label()
    if not (any(needle in label.lower() for needle in needles) or label.startswith("MESHY v002")):
        continue
    row = {
        "label": label,
        "class": actor.get_class().get_name(),
        "location_cm": [round(value, 2) for value in (actor.get_actor_location().x, actor.get_actor_location().y, actor.get_actor_location().z)],
        "rotation": [round(value, 2) for value in (actor.get_actor_rotation().roll, actor.get_actor_rotation().pitch, actor.get_actor_rotation().yaw)],
        "scale": [round(value, 4) for value in (actor.get_actor_scale3d().x, actor.get_actor_scale3d().y, actor.get_actor_scale3d().z)],
    }
    if isinstance(actor, unreal.StaticMeshActor):
        component = actor.static_mesh_component
        row["mesh"] = component.static_mesh.get_path_name() if component.static_mesh else None
        row["materials"] = [material.get_path_name() if material else None for material in component.get_materials()]
        if component.static_mesh:
            row["source_slot_names"] = [str(entry.material_slot_name) for entry in component.static_mesh.static_materials]
            row["source_slot_materials"] = [entry.material_interface.get_path_name() if entry.material_interface else None for entry in component.static_mesh.static_materials]
    rows.append(row)

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({"status": "PASS__READ_ONLY", "candidate_map": MAP, "actors": rows}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_V002_INBOUND_COMPOSITION_AUDIT_V022_PASS")
