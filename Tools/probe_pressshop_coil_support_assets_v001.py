"""Read-only bounds/material probe for existing coil support candidates."""

import json
from pathlib import Path
import unreal


PATHS = (
    "/Game/LineBoss/IndustrialKit/MaterialHandling/PR003Candidate_v011/SM_LB_CoilSaddle_Candidate_v002",
    "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002/Meshes/SM_CA_MW_PT_S01CoilCart_v001",
    "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v005/SM_CA_MW_MOD_ReceivingSaddle_v005",
)
REPORT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Saved\Audits\PressShopIntegration\pressshop_coil_support_assets_v001.json")

rows = []
for path in PATHS:
    asset = unreal.load_asset(path)
    if not isinstance(asset, unreal.StaticMesh):
        rows.append({"path": path, "found": False})
        continue
    box = asset.get_bounding_box()
    rows.append({
        "path": asset.get_path_name(),
        "found": True,
        "dimensions_cm": [round(box.max.x - box.min.x, 3), round(box.max.y - box.min.y, 3), round(box.max.z - box.min.z, 3)],
        "triangles_lod0": int(asset.get_num_triangles(0)),
        "material_slots": [str(item.material_slot_name) for item in asset.get_editor_property("static_materials")],
        "material_paths": [item.material_interface.get_path_name() if item.material_interface else None for item in asset.get_editor_property("static_materials")],
    })
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({"status": "PASS__READ_ONLY_EXISTING_ASSET_PROBE", "assets": rows}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_COIL_SUPPORT_PROBE=" + json.dumps(rows))
