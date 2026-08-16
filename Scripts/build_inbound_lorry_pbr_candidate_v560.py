"""Bind the detailed v559 lorry to controlled inbound PBR materials."""
from pathlib import Path
import json
import unreal

project = Path(unreal.Paths.project_dir())
library = unreal.EditorAssetLibrary
source = "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/LorryAssemblyCandidate_v004/SM_CA_MW_Inbound_LorryFourCoil_v004"
dest = "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/LorryAssemblyCandidate_v005/SM_CA_MW_Inbound_LorryFourCoil_v005"
if library.does_asset_exist(dest):
    library.delete_asset(dest)
if not library.duplicate_asset(source, dest):
    raise RuntimeError("Failed duplicating detailed lorry PBR candidate")
mesh = library.load_asset(dest)
if not isinstance(mesh, unreal.StaticMesh):
    raise RuntimeError("Detailed lorry PBR candidate is not a StaticMesh")

root = "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v001/Materials_v001"
bright = "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/LorryAssemblyCandidate_v003/Materials/M_CA_Inbound_BrightWrappedSteel_v001"
mapping = {
    "MI_CA_Inbound_CairnwellGreen": f"{root}/MI_CA_Inbound_CairnwellGreen_v001",
    "MI_CA_Inbound_Glass": f"{root}/MI_CA_Inbound_Glass_v001",
    "MI_CA_Inbound_Rubber": f"{root}/MI_CA_Inbound_Rubber_v001",
    "MI_CA_Inbound_Charcoal": f"{root}/MI_CA_Inbound_Charcoal_v001",
    "MI_CA_Inbound_White": f"{root}/MI_CA_Inbound_White_v001",
    "MI_CA_Inbound_BrushedSteel": bright,
    "MI_CA_Inbound_Amber": f"{root}/MI_CA_Inbound_Amber_v001",
    "MI_CA_Inbound_SafetyYellow": f"{root}/MI_CA_Inbound_SafetyYellow_v001",
    "MI_CA_Inbound_Red": f"{root}/MI_CA_Inbound_Red_v001",
    "CAI_CairnwellGreen": f"{root}/MI_CA_Inbound_CairnwellGreen_v001",
    "CAI_SensorLens": f"{root}/MI_CA_Inbound_Glass_v001",
    "CAI_CharcoalSteel": f"{root}/MI_CA_Inbound_Charcoal_v001",
    "CAI_ArchitecturalWhite": f"{root}/MI_CA_Inbound_White_v001",
    "CAI_SafetyYellow": f"{root}/MI_CA_Inbound_SafetyYellow_v001",
    "CAI_GalvanisedSteel": f"{root}/MI_CA_Inbound_BrushedSteel_v001",
    "CAI_Rubber": f"{root}/MI_CA_Inbound_Rubber_v001",
    "CAI_EStopRed": f"{root}/MI_CA_Inbound_Red_v001",
}
rows = []
for index, entry in enumerate(mesh.get_editor_property("static_materials")):
    slot = str(entry.get_editor_property("material_slot_name"))
    path = mapping.get(slot)
    if not path:
        raise RuntimeError(f"Unmapped detailed-lorry slot: {slot}")
    material = library.load_asset(path)
    if material is None:
        raise RuntimeError(f"Missing controlled material: {path}")
    mesh.set_material(index, material)
    rows.append({"index": index, "slot": slot, "material": path})
library.save_loaded_asset(mesh, only_if_is_dirty=False)

out = project / "Saved/Audits/PressShopIntegration/inbound_lorry_detailed_pbr_v560.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({
    "status": "PASS__ADDITIVE_PBR_CANDIDATE__VISUAL_GATE_REQUIRED__NOT_PROMOTED",
    "source_asset": source, "candidate_asset": dest,
    "assignments": rows,
    "bright_wrap_slots": [row for row in rows if row["material"] == bright],
    "engineering_values": "TBC", "promotion_authorized": False,
}, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_INBOUND_DETAILED_LORRY_PBR_V560_PASS")
