"""Read-only material-slot inventory for isolated inbound assets."""
from pathlib import Path
import json, unreal
DEST="/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v001"
OUT=Path(unreal.Paths.project_saved_dir())/"Audits/PressShopIntegration/inbound_material_slots_v490.json"
data={}
for path in unreal.EditorAssetLibrary.list_assets(DEST,recursive=False,include_folder=False):
    mesh=unreal.EditorAssetLibrary.load_asset(path)
    if not isinstance(mesh,unreal.StaticMesh): continue
    rows=[]
    for index,slot in enumerate(mesh.get_editor_property("static_materials")):
        mat=slot.get_editor_property("material_interface")
        rows.append({"index":index,"slot":str(slot.get_editor_property("material_slot_name")),"material":mat.get_path_name() if mat else None})
    data[path]=rows
OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(data,indent=2),encoding="utf-8")
unreal.log("LINE_BOSS_INBOUND_MATERIAL_SLOTS_V490_PASS "+str(OUT))
