"""Read-only material-slot audit for the coherent inbound lorry."""
from pathlib import Path
import json
import unreal

project = Path(unreal.Paths.project_dir())
asset_path = "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/LorryAssemblyCandidate_v001/SM_CA_MW_Inbound_LorryFourCoil_v001"
mesh = unreal.EditorAssetLibrary.load_asset(asset_path)
if not isinstance(mesh, unreal.StaticMesh):
    raise RuntimeError("Missing coherent inbound lorry")

rows = []
for index, entry in enumerate(mesh.get_editor_property("static_materials")):
    material = entry.get_editor_property("material_interface")
    rows.append({
        "index": index,
        "slot_name": str(entry.get_editor_property("material_slot_name")),
        "imported_slot_name": str(entry.get_editor_property("imported_material_slot_name")),
        "material": material.get_path_name() if material else None,
    })

out = project / "Saved/Audits/PressShopIntegration/inbound_lorry_material_slots_v542.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({"status": "READ_ONLY", "asset": asset_path, "slots": rows}, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_INBOUND_LORRY_MATERIAL_AUDIT_V542_PASS")
