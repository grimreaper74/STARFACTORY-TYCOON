"""Read-only material-slot audit for the installed protected enclosure."""
from pathlib import Path
import json
import unreal

project = Path(unreal.Paths.project_dir())
path = "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/EnclosureCandidate_v001/SM_CA_MW_Inbound_InstalledEnclosure_v001"
mesh = unreal.EditorAssetLibrary.load_asset(path)
if not isinstance(mesh, unreal.StaticMesh):
    raise RuntimeError("Missing protected enclosure")
rows = []
for index, entry in enumerate(mesh.get_editor_property("static_materials")):
    rows.append({
        "index": index,
        "slot": str(entry.get_editor_property("material_slot_name")),
        "material": entry.get_editor_property("material_interface").get_path_name()
            if entry.get_editor_property("material_interface") else None,
    })
out = project / "Saved/Audits/PressShopIntegration/inbound_enclosure_material_slots_v562.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({"asset": path, "slots": rows}, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_INBOUND_ENCLOSURE_MATERIAL_AUDIT_V562_PASS")
