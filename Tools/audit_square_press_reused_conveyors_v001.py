"""Read-only native-asset probe for press-train conveyor reuse."""
import json
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "square_meshy_press_reused_conveyors_audit_v001.json"
PATHS = {
    "interstage_roller": "/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v013/PressTrains/SM_CA_MW_InterstageRoller_Approved_v006",
    "transfer_rail": "/Game/LineBoss/Candidates/PressTrains/Shared/Presentation_v003/SM_CA_MW_PT_TransferRail_v003",
    "exit_conveyor_belt": "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002/Meshes/SM_CA_MW_PT_S07ExitConveyorBelt_v001",
    "exit_conveyor_frame": "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002/Meshes/SM_CA_MW_PT_S07ExitConveyorFrame_v001",
}

result = {}
for key, path in PATHS.items():
    asset = unreal.load_asset(path)
    if not isinstance(asset, unreal.StaticMesh):
        raise RuntimeError("SQUARE_MESHY_REUSE_AUDIT_FAIL: missing static mesh " + path)
    bounds = asset.get_bounding_box()
    result[key] = {"path": path, "triangles_lod0": int(asset.get_num_triangles(0)), "bounds_cm": [round(bounds.max.x-bounds.min.x, 3), round(bounds.max.y-bounds.min.y, 3), round(bounds.max.z-bounds.min.z, 3)], "materials": [str(slot.material_slot_name) for slot in asset.static_materials]}
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({"status": "PASS__READ_ONLY_NATIVE_CONVEYOR_REUSE_AUDIT", "assets": result}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("LINE_BOSS_SQUARE_MESHY_REUSE_AUDIT=" + json.dumps(result, sort_keys=True))
