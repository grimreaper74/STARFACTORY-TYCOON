import json
from pathlib import Path

import unreal


ASSETS = {
    "lorry": "/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v004/Inbound/SM_CA_MW_InboundLorry_Approved_v006",
    "runway": "/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/InboundInstalledCrane/Candidate_v001/SM_CA_MW_InboundCrane_StaticRunwayFrame_v001",
    "bridge": "/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/InboundInstalledCrane/Candidate_v001/SM_CA_MW_InboundCrane_MovingBridge_v001",
    "trolley": "/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/SM_LB_Crane_Trolley_v001",
    "hoist": "/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/SM_LB_Crane_HoistBlock_v001",
    "c_hook": "/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/PoweredCHook/Candidate_v035/SM_LB_Crane_PoweredCHook_Candidate_v035",
    "stand": "/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v004/Inbound/SM_CA_MW_AdjustableCoilStand_Approved_v005",
    "coil": "/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v004/Inbound/SM_CA_MW_WrappedCoil_Repaired_v003",
}

out = {}
for name, path in ASSETS.items():
    mesh = unreal.EditorAssetLibrary.load_asset(path)
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"Missing static mesh: {path}")
    bounds = mesh.get_bounds()
    out[name] = {
        "asset": path,
        "origin_cm": list(bounds.origin.to_tuple()),
        "box_extent_cm": list(bounds.box_extent.to_tuple()),
    }

destination = Path(unreal.Paths.project_saved_dir()) / "Audits/PressShopIntegration/inbound_player_package_asset_bounds_v20260810_v979.json"
destination.parent.mkdir(parents=True, exist_ok=True)
destination.write_text(json.dumps({"status": "PASS", "assets": out}, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_INBOUND_PLAYER_PACKAGE_BOUNDS_V979_PASS {destination}")
unreal.SystemLibrary.quit_editor()
