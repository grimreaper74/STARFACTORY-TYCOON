"""Create an additive lorry candidate using the controlled inbound PBR family."""
from pathlib import Path
import json
import unreal

project = Path(unreal.Paths.project_dir())
library = unreal.EditorAssetLibrary
source_path = "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/LorryAssemblyCandidate_v001/SM_CA_MW_Inbound_LorryFourCoil_v001"
dest_path = "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/LorryAssemblyCandidate_v002/SM_CA_MW_Inbound_LorryFourCoil_v002"
if library.does_asset_exist(dest_path):
    library.delete_asset(dest_path)
if not library.duplicate_asset(source_path, dest_path):
    raise RuntimeError("Failed duplicating coherent lorry to additive PBR candidate")

mesh = library.load_asset(dest_path)
if not isinstance(mesh, unreal.StaticMesh):
    raise RuntimeError("Duplicated lorry is not a StaticMesh")

material_root = "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v001/Materials_v001"
mapping = {
    "MI_CA_Inbound_CairnwellGreen": "MI_CA_Inbound_CairnwellGreen_v001",
    "MI_CA_Inbound_Glass": "MI_CA_Inbound_Glass_v001",
    "MI_CA_Inbound_Rubber": "MI_CA_Inbound_Rubber_v001",
    "MI_CA_Inbound_Charcoal": "MI_CA_Inbound_Charcoal_v001",
    "MI_CA_Inbound_White": "MI_CA_Inbound_White_v001",
    "MI_CA_Inbound_BrushedSteel": "MI_CA_Inbound_BrushedSteel_v001",
    "MI_CA_Inbound_Amber": "MI_CA_Inbound_Amber_v001",
    "MI_CA_Inbound_SafetyYellow": "MI_CA_Inbound_SafetyYellow_v001",
    "MI_CA_Inbound_Red": "MI_CA_Inbound_Red_v001",
}
rows = []
for index, entry in enumerate(mesh.get_editor_property("static_materials")):
    slot = str(entry.get_editor_property("material_slot_name"))
    target_name = mapping.get(slot)
    if not target_name:
        raise RuntimeError(f"Unmapped coherent-lorry slot: {slot}")
    material = library.load_asset(f"{material_root}/{target_name}")
    if material is None:
        raise RuntimeError(f"Missing controlled material: {target_name}")
    mesh.set_material(index, material)
    rows.append({"index": index, "slot": slot, "material": material.get_path_name()})

library.save_loaded_asset(mesh, only_if_is_dirty=False)
out = project / "Saved/Audits/PressShopIntegration/inbound_lorry_pbr_candidate_v543.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({
    "status": "PASS__ADDITIVE_PBR_CANDIDATE__VISUAL_GATE_REQUIRED__NOT_PROMOTED",
    "source_asset": source_path,
    "candidate_asset": dest_path,
    "slot_count": len(rows),
    "assignments": rows,
    "engineering_values": "TBC",
    "promotion_authorized": False,
}, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_INBOUND_LORRY_PBR_V543_PASS")
