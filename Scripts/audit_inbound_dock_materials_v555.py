"""Read-only material-slot audit for isolated dock v002."""
from pathlib import Path
import json
import unreal

project = Path(unreal.Paths.project_dir())
path = "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/DockArchitectureCandidate_v002/SM_CA_MW_Inbound_DockArchitecture_v002"
mesh = unreal.EditorAssetLibrary.load_asset(path)
if not isinstance(mesh, unreal.StaticMesh):
    raise RuntimeError("Missing dock architecture v002")
rows = []
for index, slot in enumerate(mesh.get_editor_property("static_materials")):
    mat = mesh.get_material(index)
    rows.append({
        "index": index,
        "slot": str(slot.get_editor_property("material_slot_name")),
        "imported_slot": str(slot.get_editor_property("imported_material_slot_name")),
        "effective_material": mat.get_path_name() if mat else None,
    })
out = project / "Saved/Audits/PressShopIntegration/inbound_dock_material_slots_v555.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({"asset": path, "slots": rows}, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_INBOUND_DOCK_MATERIAL_AUDIT_V555_PASS")
