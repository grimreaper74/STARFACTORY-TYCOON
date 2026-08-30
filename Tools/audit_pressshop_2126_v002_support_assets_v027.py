"""Read-only audit of existing project support assets for the v002 candidate."""
import json
from pathlib import Path

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_v002_support_assets_v027.json"
ASSETS = (
    ("outfeed_conveyor", "/Game/LineBoss/Developer/Validation/PressTrains/CompleteTrainA_v662/Supports/SM_CA_MW_PTA_S06S07_PoweredConveyor_SupportAsset_06_v661"),
    ("inspection_unload", "/Game/LineBoss/Developer/Validation/PressTrains/CompleteTrainA_v662/Supports/SM_CA_MW_PTA_S07_InspectUnload_SupportAsset_11_v661"),
    ("flat_panel_stillage", "/Game/LineBoss/Developer/Validation/PressTrains/CompleteTrainA_v662/Supports/SM_CA_MW_PTA_S07_FlatPanelStillage_SupportAsset_05_v661"),
    ("destack_blank_feed", "/Game/LineBoss/Developer/Validation/PressTrains/CompleteTrainA_v662/Supports/SM_CA_MW_PTA_S01_DestackBlankFeed_SupportAsset_08_v661"),
    ("presentation_unload_cell", "/Game/LineBoss/Candidates/PressTrains/Shared/Presentation_v003/SM_CA_MW_PT_UnloadInspectCell_v003"),
    ("presentation_transfer_rail", "/Game/LineBoss/Candidates/PressTrains/Shared/Presentation_v003/SM_CA_MW_PT_TransferRail_v003"),
    ("presentation_destack_lift", "/Game/LineBoss/Candidates/PressTrains/Shared/Presentation_v003/SM_CA_MW_PT_DestackLift_v003"),
)

rows = []
for role, path in ASSETS:
    asset = unreal.load_asset(path)
    if not isinstance(asset, unreal.StaticMesh):
        raise RuntimeError("Expected StaticMesh unavailable for %s: %s" % (role, path))
    bounds = asset.get_bounds()
    slots = asset.static_materials
    rows.append({
        "role": role,
        "asset": asset.get_path_name(),
        "extent_cm": [round(bounds.box_extent.x, 2), round(bounds.box_extent.y, 2), round(bounds.box_extent.z, 2)],
        "origin_cm": [round(bounds.origin.x, 2), round(bounds.origin.y, 2), round(bounds.origin.z, 2)],
        "material_slots": [str(slot.material_slot_name) for slot in slots],
        "slot_materials": [slot.material_interface.get_path_name() if slot.material_interface else None for slot in slots],
    })

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({"status": "PASS__SOURCE_ASSETS_READ_ONLY", "assets": rows}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_V002_SUPPORT_ASSET_AUDIT_V027_PASS")
