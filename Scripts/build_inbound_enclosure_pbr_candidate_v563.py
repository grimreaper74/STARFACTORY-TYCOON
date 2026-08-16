"""Create an additive controlled-PBR protected-enclosure candidate."""
from pathlib import Path
import json
import unreal

project = Path(unreal.Paths.project_dir())
library = unreal.EditorAssetLibrary
source = "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/EnclosureCandidate_v001/SM_CA_MW_Inbound_InstalledEnclosure_v001"
dest = "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/EnclosureCandidate_v002/SM_CA_MW_Inbound_InstalledEnclosure_v002"
if library.does_asset_exist(dest):
    library.delete_asset(dest)
if not library.duplicate_asset(source, dest):
    raise RuntimeError("Failed duplicating protected enclosure")
mesh = library.load_asset(dest)
if not isinstance(mesh, unreal.StaticMesh):
    raise RuntimeError("Protected-enclosure candidate is not a StaticMesh")
root = "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v001/Materials_v001"
mapping = {
    "CAI_Charcoal": "MI_CA_Inbound_Charcoal_v001",
    "CAI_EStopRed": "MI_CA_Inbound_Red_v001",
    "CAI_SafetyYellow": "MI_CA_Inbound_SafetyYellow_v001",
    "CAI_CairnwellGreen": "MI_CA_Inbound_CairnwellGreen_v001",
    "CAI_SensorLens": "MI_CA_Inbound_Glass_v001",
}
rows = []
for index, entry in enumerate(mesh.get_editor_property("static_materials")):
    slot = str(entry.get_editor_property("material_slot_name"))
    target = mapping.get(slot)
    if not target:
        raise RuntimeError(f"Unmapped enclosure slot: {slot}")
    material = library.load_asset(f"{root}/{target}")
    if material is None:
        raise RuntimeError(f"Missing controlled material: {target}")
    mesh.set_material(index, material)
    rows.append({"index": index, "slot": slot, "material": material.get_path_name()})
library.save_loaded_asset(mesh, only_if_is_dirty=False)
out = project / "Saved/Audits/PressShopIntegration/inbound_enclosure_pbr_candidate_v563.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({
    "status": "PASS__ADDITIVE_PBR_CANDIDATE__VISUAL_GATE_REQUIRED__NOT_PROMOTED",
    "source_asset": source, "candidate_asset": dest, "assignments": rows,
    "engineering_values": "TBC", "promotion_authorized": False,
}, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_INBOUND_ENCLOSURE_PBR_V563_PASS")
