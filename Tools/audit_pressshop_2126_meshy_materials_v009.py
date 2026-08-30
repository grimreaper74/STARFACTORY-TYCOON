"""Read-only material-slot audit for the five real Meshy press components."""

import json
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
REPORT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Saved\Audits\PressShopIntegration\pressshop_2126_meshy_materials_v009.json")
PREFIX = "MESHY | S0"


if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load fresh candidate map")

rows = []
for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    label = actor.get_actor_label()
    if not label.startswith(PREFIX) or "reused press asset" not in label:
        continue
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    if component is None or not isinstance(component.static_mesh, unreal.StaticMesh):
        raise RuntimeError("Expected StaticMeshComponent on " + label)
    mesh = component.static_mesh
    materials = []
    for index, material in enumerate(component.get_materials()):
        materials.append({
            "index": index,
            "component_material": material.get_path_name() if material else None,
        })
    rows.append({
        "actor": label,
        "mesh": mesh.get_path_name(),
        "material_slots": materials,
    })

if len(rows) != 5:
    raise RuntimeError("Expected five real Meshy press actors, found %d" % len(rows))
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({"status": "PASS__READ_ONLY_MESHY_MATERIAL_SLOT_AUDIT", "presses": rows}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_MESHY_MATERIAL_AUDIT_V009_PASS")
