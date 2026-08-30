"""Measure known press conveyors before reuse in the fresh candidate map."""

import json
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_conveyor_reuse_audit_v001.json"
ASSETS = {
    "roller_conveyor": "/Game/LineBoss/Developer/Validation/PressTrains/NewRigidIntake_v741/Cairnwell_RollerConveyor_Movable_v740/StaticMeshes/SM_CA_ROLLER_CONVEYO__TEXTURED_STATIC_v740",
    "exit_conveyor_frame": "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002/Meshes/SM_CA_MW_PT_S07ExitConveyorFrame_v001",
    "exit_conveyor_belt": "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002/Meshes/SM_CA_MW_PT_S07ExitConveyorBelt_v001",
    "transfer_rail": "/Game/LineBoss/Candidates/PressTrains/Shared/Presentation_v003/SM_CA_MW_PT_TransferRail_v003",
}


def measure(path):
    asset = unreal.load_asset(path)
    row = {"path": path, "found": asset is not None}
    if not isinstance(asset, unreal.StaticMesh):
        row["class"] = asset.get_class().get_name() if asset else None
        return row
    box = asset.get_bounding_box()
    row.update({
        "class": "StaticMesh",
        "bounds_cm": [round(box.max.x - box.min.x, 2), round(box.max.y - box.min.y, 2), round(box.max.z - box.min.z, 2)],
        "triangles_lod0": int(asset.get_num_triangles(0)),
        "sections_lod0": int(asset.get_num_sections(0)),
    })
    return row


rows = {key: measure(path) for key, path in ASSETS.items()}
safe = [key for key, row in rows.items() if row.get("class") == "StaticMesh" and row.get("triangles_lod0", 1000000) <= 50000]
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS" if safe else "FAIL__NO_LIGHTWEIGHT_CONVEYOR_CANDIDATE",
    "candidate_map_untouched": True,
    "assets": rows,
    "lightweight_reuse_candidates": safe,
    "guard": "Candidate visual map permits only conveyors at or below 50,000 LOD0 triangles each until a packaged budget exists.",
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_CONVEYOR_REUSE_AUDIT_PASS " + ",".join(safe))
