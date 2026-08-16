"""Read-only slot audit for installed inbound crane modules."""
from pathlib import Path
import json
import unreal

project = Path(unreal.Paths.project_dir())
paths = [
    "/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/InboundInstalledCrane/Candidate_v001/SM_CA_MW_InboundCrane_StaticRunwayFrame_v001",
    "/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/InboundInstalledCrane/Candidate_v001/SM_CA_MW_InboundCrane_MovingBridge_v001",
    "/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/SM_LB_Crane_Trolley_v001",
    "/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/SM_LB_Crane_HoistBlock_v001",
    "/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/PoweredCHook/Candidate_v035/SM_LB_Crane_PoweredCHook_Candidate_v035",
]
assets = []
for path in paths:
    mesh = unreal.EditorAssetLibrary.load_asset(path)
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"Missing crane mesh: {path}")
    rows = []
    for index, entry in enumerate(mesh.get_editor_property("static_materials")):
        material = entry.get_editor_property("material_interface")
        rows.append({
            "index": index,
            "slot": str(entry.get_editor_property("material_slot_name")),
            "material": material.get_path_name() if material else None,
        })
    size = mesh.get_bounds().box_extent * 2
    assets.append({"asset": path, "bounds_cm": [float(size.x), float(size.y), float(size.z)], "slots": rows})
out = project / "Saved/Audits/PressShopIntegration/inbound_crane_material_slots_v565.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({"assets": assets}, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_INBOUND_CRANE_MATERIAL_AUDIT_V565_PASS")
