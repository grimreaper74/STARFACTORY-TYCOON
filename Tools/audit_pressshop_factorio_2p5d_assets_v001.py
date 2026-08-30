"""Read-only audit of assets available for the full 2.5D Press Shop."""
import hashlib
import json
from pathlib import Path

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_factorio_2p5d_assets_v001.json"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
V002 = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap"
ASSETS = {
    "S01_coil_free_feeder": "/Game/LineBoss/Candidates/PressShop/MeshyCoilFeederNoCoil_v001/SM_LB_PS_InfeedCoilFeeder_NoCoil_v001",
    "S02_new_portal_press": "/Game/LineBoss/Candidates/PressShop/S02PortalPressMeshyClean_v002/SM_LB_PS_S02_PortalPress_MeshyClean_v002",
    "S03_trim": "/Game/LineBoss/Candidates/PressShop/SquareMeshyPressTrain_v001/SM_LB_PS_S03_Trim_MeshyClean_v001",
    "S04_pierce": "/Game/LineBoss/Candidates/PressShop/SquareMeshyPressTrain_v001/SM_LB_PS_S04_Pierce_MeshyClean_v001",
    "S05_flange_hem": "/Game/LineBoss/Candidates/PressShop/SquareMeshyPressTrain_v001/SM_LB_PS_S05_FlangeHem_MeshyClean_v001",
    "S06_vision_outfeed": "/Game/LineBoss/Candidates/PressShop/SquareMeshyPressTrain_v001/SM_LB_PS_S06_VisionOutfeed_MeshyClean_v001",
    "powered_conveyor": "/Game/LineBoss/Developer/Validation/PressTrains/CompleteTrainA_v662/Supports/SM_CA_MW_PTA_S06S07_PoweredConveyor_SupportAsset_06_v661",
    "inspection_unload": "/Game/LineBoss/Developer/Validation/PressTrains/CompleteTrainA_v662/Supports/SM_CA_MW_PTA_S07_InspectUnload_SupportAsset_11_v661",
    "panel_stillage": "/Game/LineBoss/Developer/Validation/PressTrains/CompleteTrainA_v662/Supports/SM_CA_MW_PTA_S07_FlatPanelStillage_SupportAsset_05_v661",
    "bare_coil": "/Game/LineBoss/IndustrialKit/MaterialHandling/BareCoil/Candidate_v021/SM_LB_BareMasterCoil_v021",
    "wrapped_coil": "/Game/LineBoss/IndustrialKit/MaterialHandling/MasterCoil/Candidate_v005/SM_LB_MasterCoil_Candidate_v005",
    "coil_saddle": "/Game/LineBoss/IndustrialKit/MaterialHandling/PR003Candidate_v011/SM_LB_CoilSaddle_Candidate_v002",
    "robot_tender": "/Game/Meshes/Robot/SM_RoboArm04",
}


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def uasset_file(path):
    return PROJECT / "Content" / (path.removeprefix("/Game/").replace("/", "\\") + ".uasset")


protected_before = {"v438": sha256(PROTECTED), "v002": sha256(V002)}
records = {}
for role, path in ASSETS.items():
    mesh = unreal.load_asset(path)
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError("asset unavailable: " + role)
    disk = uasset_file(path)
    if not disk.is_file():
        raise RuntimeError("uasset missing: " + role)
    extent = mesh.get_bounds().box_extent
    records[role] = {
        "asset": path,
        "dimensions_cm": [round(extent.x * 2.0, 2), round(extent.y * 2.0, 2), round(extent.z * 2.0, 2)],
        "material_slots": [str(item) for item in mesh.get_editor_property("static_materials")],
        "source_sha256": sha256(disk),
    }
protected_after = {"v438": sha256(PROTECTED), "v002": sha256(V002)}
if protected_before != protected_after:
    raise RuntimeError("a protected map changed during a read-only asset audit")
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__READ_ONLY_FULL_2P5D_ASSET_AUDIT",
    "assets": records,
    "protected_hashes_before": protected_before,
    "protected_hashes_after": protected_after,
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_FACTORIO_2P5D_ASSET_AUDIT_PASS assets=" + str(len(records)))
