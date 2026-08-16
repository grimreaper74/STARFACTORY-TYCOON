"""Create additive controlled-PBR inbound runway and moving-bridge assets."""
from pathlib import Path
import json
import unreal

project = Path(unreal.Paths.project_dir())
library = unreal.EditorAssetLibrary
root = "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v001/Materials_v001"
source_root = "/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/InboundInstalledCrane/Candidate_v001"
dest_root = "/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/InboundInstalledCrane/Candidate_v002"
specs = [
    ("SM_CA_MW_InboundCrane_StaticRunwayFrame_v001", "SM_CA_MW_InboundCrane_StaticRunwayFrame_v002"),
    ("SM_CA_MW_InboundCrane_MovingBridge_v001", "SM_CA_MW_InboundCrane_MovingBridge_v002"),
]
mapping = {
    "CA_InboundCrane_DarkSteel": "MI_CA_Inbound_Charcoal_v001",
    "CA_InboundCrane_RAL1023": "MI_CA_Inbound_SafetyYellow_v001",
    "CA_InboundCrane_MachinedSteel": "MI_CA_Inbound_BrushedSteel_v001",
    "CA_InboundCrane_Rubber": "MI_CA_Inbound_Rubber_v001",
    "CA_InboundCrane_StatusGreen": "MI_CA_Inbound_Glass_v001",
}
records = []
for source_name, dest_name in specs:
    source = f"{source_root}/{source_name}"
    dest = f"{dest_root}/{dest_name}"
    if library.does_asset_exist(dest):
        library.delete_asset(dest)
    if not library.duplicate_asset(source, dest):
        raise RuntimeError(f"Failed duplicating crane module: {source_name}")
    mesh = library.load_asset(dest)
    rows = []
    for index, entry in enumerate(mesh.get_editor_property("static_materials")):
        slot = str(entry.get_editor_property("material_slot_name"))
        target = mapping.get(slot)
        if not target:
            raise RuntimeError(f"Unmapped crane slot: {slot}")
        material = library.load_asset(f"{root}/{target}")
        if material is None:
            raise RuntimeError(f"Missing controlled crane material: {target}")
        mesh.set_material(index, material)
        rows.append({"index": index, "slot": slot, "material": material.get_path_name()})
    library.save_loaded_asset(mesh, only_if_is_dirty=False)
    records.append({"source": source, "candidate": dest, "assignments": rows})
out = project / "Saved/Audits/PressShopIntegration/inbound_crane_pbr_candidate_v566.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({
    "status": "PASS__ADDITIVE_PBR_CANDIDATES__VISUAL_GATE_REQUIRED__NOT_PROMOTED",
    "records": records, "powered_chook": "retained Candidate_v035",
    "engineering_values": "TBC", "promotion_authorized": False,
}, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_INBOUND_CRANE_PBR_V566_PASS")
