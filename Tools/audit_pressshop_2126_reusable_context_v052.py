"""Read-only suitability audit of reusable production-context meshes."""

import json
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_reusable_context_v052.json"
ASSETS = (
    "/Game/LineBoss/Candidates/PressTrains/Shared/Presentation_v003/SM_CA_MW_PT_UnloadInspectCell_v003.SM_CA_MW_PT_UnloadInspectCell_v003",
    "/Game/LineBoss/Candidates/PressTrains/Shared/Presentation_v003/SM_CA_MW_PT_TransferRail_v003.SM_CA_MW_PT_TransferRail_v003",
    "/Game/LineBoss/Candidates/PressTrains/Shared/Presentation_v003/SM_CA_MW_PT_DestackLoadCell_v003.SM_CA_MW_PT_DestackLoadCell_v003",
    "/Game/LineBoss/Candidates/PressTrains/Shared/Presentation_v003/SM_CA_MW_PT_DestackLift_v003.SM_CA_MW_PT_DestackLift_v003",
    "/Game/LineBoss/Candidates/PressTrains/Shared/Presentation_v003/SM_CA_MW_PT_CommonUtilitySpine_v003.SM_CA_MW_PT_CommonUtilitySpine_v003",
    "/Game/LineBoss/Candidates/PressTrains/Shared/Presentation_v003/SM_CA_MW_PT_CommonPlatform_v003.SM_CA_MW_PT_CommonPlatform_v003",
    "/Game/LineBoss/Candidates/PressShop/IntakeRework_v001/SM_LB_Press_DestackMagazine_v002.SM_LB_Press_DestackMagazine_v002",
)

rows = []
for path in ASSETS:
    mesh = unreal.load_asset(path)
    if not isinstance(mesh, unreal.StaticMesh):
        rows.append({"path": path, "status": "MISSING_OR_NOT_STATIC_MESH"})
        continue
    bounds = mesh.get_bounds()
    materials = []
    for index in range(mesh.get_num_sections(0)):
        material = mesh.get_material(index)
        if material and material.get_path_name() not in materials:
            materials.append(material.get_path_name())
    rows.append({
        "path": path,
        "status": "AVAILABLE",
        "size_cm": [round(bounds.box_extent.x * 2, 1), round(bounds.box_extent.y * 2, 1), round(bounds.box_extent.z * 2, 1)],
        "materials": materials,
        "lod0_sections": mesh.get_num_sections(0),
    })
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({"status": "PASS__READ_ONLY_REUSABLE_CONTEXT_AUDIT", "assets": rows}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_REUSABLE_CONTEXT_AUDIT_V052_PASS")
