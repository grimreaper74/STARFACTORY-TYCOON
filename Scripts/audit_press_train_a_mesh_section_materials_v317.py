"""Read-only audit of LOD0 section-to-slot usage for the combined Train A mesh."""
import json
from collections import Counter
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir());OUT=ROOT/"Saved/Audits/PressTrains/press_train_a_mesh_section_materials_v317.json"
mesh=unreal.load_asset("/Game/LineBoss/Candidates/PressTrains/TrainA/ModularVisual_v302/SM_CA_MW_PressTrainA_ModularAssembly_v037")
sub=unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
rows=[]
for section in range(1024):
 try:
  slot=sub.get_lod_material_slot(mesh,0,section)
 except Exception:
  break
 if slot is None or int(slot)<0:break
 rows.append({"section":section,"slot":int(slot)})
payload={"section_count":len(rows),"unique_slot_count":len(set(r["slot"] for r in rows)),"slot_histogram":dict(Counter(str(r["slot"]) for r in rows)),"sections":rows}
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,indent=2),encoding="utf-8");print(json.dumps(payload,indent=2));unreal.SystemLibrary.quit_editor()
