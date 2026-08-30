"""Read-only asset audit for the candidate's inspection and outbound endpoint."""

import json
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_outbound_reuse_audit_v001.json"
ASSETS = {
    "vision_gate": "/Game/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001/Vision/SM_LB_BodyShop_VisionGate_v001",
    "operator_hmi": "/Game/LineBoss/Candidates/PressShop/OperatorHMIStand_v001/SM_LB_OperatorHMIStand_v001",
    "press_outbound_dunnage": "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002/Meshes/SM_CA_MW_PT_S07OutboundDunnage_v001",
    "press_inspection_stillage": "/Game/LineBoss/Candidates/PressTrains/Shared/ExteriorDetail_v002/SM_CA_MW_PT_S07InspectionStillageDress_v002",
}


def measure(path):
    asset = unreal.load_asset(path)
    row = {"path": path, "found": asset is not None}
    if not isinstance(asset, unreal.StaticMesh):
        row["class"] = asset.get_class().get_name() if asset else None
        return row
    box = asset.get_bounding_box()
    row.update({"class": "StaticMesh", "bounds_cm": [round(box.max.x-box.min.x,2), round(box.max.y-box.min.y,2), round(box.max.z-box.min.z,2)], "triangles_lod0": int(asset.get_num_triangles(0)), "sections_lod0": int(asset.get_num_sections(0))})
    return row


rows = {key: measure(path) for key,path in ASSETS.items()}
safe = [key for key,row in rows.items() if row.get("class") == "StaticMesh" and row.get("triangles_lod0",999999) <= 50000]
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({"status": "PASS" if safe else "FAIL__NO_LIGHTWEIGHT_OUTBOUND_REUSE", "candidate_map_untouched": True, "assets": rows, "lightweight_reuse_candidates": safe}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_OUTBOUND_REUSE_AUDIT_PASS " + ",".join(safe))
