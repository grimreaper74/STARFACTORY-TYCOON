"""Read-only material-slot audit for the native square-press candidate meshes."""

import json
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
ROOT = "/Game/LineBoss/Candidates/PressShop/SquareMeshyPressTrain_v001"
OUTPUT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "square_meshy_press_material_slots_v001.json"
ASSETS = {
    "S02_DrawForm": ROOT + "/SM_LB_PS_S02_DrawForm_MeshyClean_v001",
    "S03_Trim": ROOT + "/SM_LB_PS_S03_Trim_MeshyClean_v001",
    "S04_Pierce": ROOT + "/SM_LB_PS_S04_Pierce_MeshyClean_v001",
    "S05_FlangeHem": ROOT + "/SM_LB_PS_S05_FlangeHem_MeshyClean_v001",
    "S06_VisionOutfeed": ROOT + "/SM_LB_PS_S06_VisionOutfeed_MeshyClean_v001",
}


def material_path(material):
    return material.get_path_name() if material else None


results = {}
for label, path in ASSETS.items():
    mesh = unreal.load_asset(path)
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError("Missing native press mesh: " + path)
    materials = mesh.get_editor_property("static_materials")
    results[label] = {
        "asset": path,
        "material_slots": [
            {
                "slot_name": str(slot.get_editor_property("material_slot_name")),
                "material": material_path(slot.get_editor_property("material_interface")),
            }
            for slot in materials
        ],
    }

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("LINE_BOSS_SQUARE_MESHY_PRESS_MATERIAL_AUDIT=" + json.dumps(results, sort_keys=True))
