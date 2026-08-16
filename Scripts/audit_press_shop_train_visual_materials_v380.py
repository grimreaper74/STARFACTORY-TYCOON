"""Read-only exact-v374 material inventory for the four visual train aggregates."""
from datetime import datetime, timezone
import json
from pathlib import Path
import unreal

MAP="/Game/LineBoss/Maps/LB_PressShop_WideSpanTrussCandidate_v374"
ROOT=Path(unreal.Paths.project_dir());OUT=ROOT/"Saved/Audits/PressShopIntegration/press_shop_train_visual_materials_v381.json"
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):raise RuntimeError(MAP)
rows=[]
for actor in actors.get_all_level_actors():
 tags={str(t) for t in actor.tags}
 if not any("ProDetail" in t for t in tags):continue
 comp=actor.get_component_by_class(unreal.StaticMeshComponent)
 if comp is None:continue
 mesh=comp.static_mesh
 materials=[]
 for i in range(comp.get_num_materials()):
  mat=comp.get_material(i)
  materials.append({"slot":i,"material":mat.get_path_name() if mat else None})
 rows.append({"actor":actor.get_actor_label(),"location_cm":list(actor.get_actor_location().to_tuple()),
              "mesh":mesh.get_path_name() if mesh else None,"material_slots":materials,
              "tags":sorted(tags)})
payload={"$schema":"cairnwell/audit/press-shop-train-visual-materials-v381/v1","generated_utc":datetime.now(timezone.utc).isoformat(),"status":"PASS__READ_ONLY_FOUR_TRAIN_VISUAL_MATERIAL_INVENTORY" if len(rows)==4 else "FAIL__VISUAL_TRAIN_COUNT","map":MAP,"map_saved":False,"visual_train_count":len(rows),"visual_trains":rows,"promotion_authorized":False}
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8');print(json.dumps(payload,indent=2));unreal.SystemLibrary.quit_editor()
