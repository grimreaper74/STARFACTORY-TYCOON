"""Read-only audit of reusable context assets for the isolated press review.

This is deliberately an audit, not a placement script.  It establishes the
actual Unreal payloads and their scale before an upstream / downstream context
pass is allowed to reuse them.
"""
import json
from pathlib import Path

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
OUT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "press_train_context_asset_audit_v001.json"
ASSETS = {
    "S01 decoiler base": "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002/Meshes/SM_CA_MW_PT_S01DecoilerBase_v001",
    "S01 decoiler spindle": "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002/Meshes/SM_CA_MW_PT_S01DecoilerSpindle_v001",
    "S01 straightener feed": "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002/Meshes/SM_CA_MW_PT_S01StraightenerFeed_v001",
    "S01 feed bridge": "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002/Meshes/SM_CA_MW_PT_S01FeedBridge_v001",
    "S07 inspection cell": "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002/Meshes/SM_CA_MW_PT_S07InspectionCell_v001",
    "S07 outbound dunnage": "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002/Meshes/SM_CA_MW_PT_S07OutboundDunnage_v001",
    "Coil AGV core reference": "/Game/LineBoss/Developer/Validation/EngineComparison/CoilAGV_Untouched_v20260810/SM_Cairnwell_CoilAGV_Untouched_v20260810",
    "Overhead crane candidate": "/Game/Meshes/Crane/SM_Crane01",
}

report = {"status": "PASS__READ_ONLY_REUSE_AUDIT", "assets": {}}
for label, path in ASSETS.items():
    asset = unreal.load_asset(path)
    if asset is None:
        raise RuntimeError("PRESS_CONTEXT_AUDIT_FAIL missing asset: " + path)
    entry = {"path": path, "class": asset.get_class().get_name()}
    if isinstance(asset, unreal.StaticMesh):
        bounds = asset.get_bounds()
        entry["size_cm"] = [round(bounds.box_extent.x * 2.0, 3), round(bounds.box_extent.y * 2.0, 3), round(bounds.box_extent.z * 2.0, 3)]
        try:
            entry["triangles_lod0"] = int(asset.get_num_triangles(0))
        except Exception:
            entry["triangles_lod0"] = "UNAVAILABLE"
        entry["material_slots"] = [str(slot.material_slot_name) for slot in asset.static_materials]
    report["assets"][label] = entry

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("PRESS_CONTEXT_AUDIT=" + json.dumps(report, sort_keys=True))
