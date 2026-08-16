"""Create isolated dock v003 by binding controlled inbound PBR materials to v002 geometry."""
from pathlib import Path
import hashlib
import json
import unreal

project = Path(unreal.Paths.project_dir())
library = unreal.EditorAssetLibrary
source = "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/DockArchitectureCandidate_v002/SM_CA_MW_Inbound_DockArchitecture_v002"
dest_dir = "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/DockArchitectureCandidate_v003"
dest = dest_dir + "/SM_CA_MW_Inbound_DockArchitecture_v003"
if library.does_asset_exist(dest):
    library.delete_asset(dest)
mesh = library.duplicate_asset(source, dest)
if not isinstance(mesh, unreal.StaticMesh):
    raise RuntimeError("Could not duplicate dock v002 to isolated v003")

material_paths = {
    "CAI_CharcoalSteel": "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v001/Materials_v001/MI_CA_Inbound_Charcoal_v001",
    "CAI_SafetyYellow": "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v001/Materials_v001/MI_CA_Inbound_SafetyYellow_v001",
    "CAI_EStopRed": "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v001/Materials_v001/MI_CA_Inbound_Red_v001",
    "CAI_CairnwellGreen": "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v001/Materials_v001/MI_CA_Inbound_CairnwellGreen_v001",
    "CAI_GalvanisedSteel": "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v001/Materials_v001/MI_CA_Inbound_BrushedSteel_v001",
    "CAI_Rubber": "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v001/Materials_v001/MI_CA_Inbound_Rubber_v001",
    "CAI_SensorLens": "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v001/Materials_v001/MI_CA_Inbound_Glass_v001",
    "CAI_ArchitecturalWhite": "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v001/Materials_v001/MI_CA_Inbound_White_v001",
}
bound = []
for index, slot in enumerate(mesh.get_editor_property("static_materials")):
    slot_name = str(slot.get_editor_property("material_slot_name"))
    path = material_paths.get(slot_name)
    mat = library.load_asset(path) if path else None
    if mat is None:
        raise RuntimeError(f"No controlled PBR material for dock slot {slot_name}")
    mesh.set_material(index, mat)
    bound.append({"index": index, "slot": slot_name, "material": path})

unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
library.save_loaded_asset(mesh, only_if_is_dirty=False)
size = mesh.get_bounds().box_extent * 2
body = mesh.get_editor_property("body_setup") is not None
audit = project / "Saved/Audits/PressShopIntegration/inbound_dock_pbr_candidate_v556.json"
audit.parent.mkdir(parents=True, exist_ok=True)
source_fbx = project / "SourceAssets/Candidate/PressShop/InboundCoilDelivery/DockArchitecture_v002/SM_CA_MW_Inbound_DockArchitecture_v002.fbx"
audit.write_text(json.dumps({
    "status": "PASS__ISOLATED_MATERIAL_BINDING_ONLY__NOT_PROMOTED",
    "asset": dest,
    "geometry_source": source,
    "source_fbx_sha256": hashlib.sha256(source_fbx.read_bytes()).hexdigest(),
    "bounds_cm": [round(float(size.x), 3), round(float(size.y), 3), round(float(size.z), 3)],
    "has_body_setup": body,
    "bindings": bound,
    "engineering_values": "TBC",
    "promotion_authorized": False
}, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_INBOUND_DOCK_PBR_CANDIDATE_V556_BUILD_PASS")
