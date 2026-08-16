"""Rebind the aligned v038 shell to retained Cairnwell Train A PBR materials."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()); BASE="/Game/LineBoss/Maps/LB_PressTrainAPresentationShellCandidate_v038"; MAP="/Game/LineBoss/Maps/LB_PressTrainAPresentationShellMaterialCandidate_v039"; BASE_FILE=ROOT/"Content/LineBoss/Maps/LB_PressTrainAPresentationShellCandidate_v038.umap"; MAP_FILE=ROOT/"Content/LineBoss/Maps/LB_PressTrainAPresentationShellMaterialCandidate_v039.umap"; OUT=ROOT/"Saved/Audits/PressTrains/press_train_a_presentation_shell_material_build_v039.json"
lib=unreal.EditorAssetLibrary; levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); api=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
MATS={"charcoal":"/Game/LineBoss/Candidates/PressTrains/TrainA/AssemblyStudyIntegration_v004/Materials/M_CA_MW_PTA_Charcoal_Integration_v004","green":"/Game/LineBoss/Candidates/PressTrains/TrainA/AssemblyStudyIntegration_v004/Materials/M_CA_MW_PTA_Green_Integration_v004","steel":"/Game/LineBoss/Candidates/PressTrains/TrainA/AssemblyStudyIntegration_v004/Materials/M_CA_MW_PTA_WorkedSteel_Integration_v004","yellow":"/Game/LineBoss/Candidates/PressTrains/TrainA/AssemblyStudyIntegration_v004/Materials/M_CA_MW_PTA_SafetyYellow_Integration_v004"}
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
 return h.hexdigest().upper()
if lib.does_asset_exist(MAP) or OUT.exists(): raise RuntimeError("refusing to overwrite v039")
base_hash=sha(BASE_FILE)
loaded={k:lib.load_asset(v) for k,v in MATS.items()}
if not all(isinstance(v,unreal.MaterialInterface) for v in loaded.values()): raise RuntimeError("retained material missing")
if not levels.new_level_from_template(MAP,BASE): raise RuntimeError("fresh v038 material child failed")
a=next((x for x in api.get_all_level_actors() if x.get_actor_label()=="CA_MW_PTA_PresentationShell_v014_FIXED_CM"),None)
if not isinstance(a,unreal.StaticMeshActor): raise RuntimeError("aligned shell actor missing")
c=a.static_mesh_component; slots=c.static_mesh.get_editor_property("static_materials"); rows=[]; fail=[]
for i,s in enumerate(slots):
 name=str(s.material_slot_name).lower()
 if "green" in name: key="green"
 elif "yellow" in name: key="yellow"
 elif "workedsteel" in name or ("steel" in name and "dark" not in name): key="steel"
 elif "dark" in name or "charcoal" in name: key="charcoal"
 else: key=None
 if key is None: fail.append(f"unmapped slot {i}:{name}"); continue
 c.set_material(i,loaded[key]); rows.append({"index":i,"slot":str(s.material_slot_name),"material_key":key,"material":loaded[key].get_path_name()})
c.set_collision_profile_name(unreal.Name("NoCollision"),True); c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION); c.set_editor_property("can_ever_affect_navigation",False)
a.tags=list(a.tags)+[unreal.Name("LB.PressTrain.PresentationShell.Materials.v039"),unreal.Name("LB.Asset.Candidate.v039")]
if len(rows)!=len(slots): fail.append(f"mapped {len(rows)} of {len(slots)} slots")
if str(c.get_collision_profile_name())!="NoCollision": fail.append("collision profile changed")
if not levels.save_current_level(): fail.append("save failed")
if sha(BASE_FILE)!=base_hash: fail.append("v038 parent changed")
p={"status":"PASS__ALIGNED_V014_SHELL_WITH_RETAINED_CAIRNWELL_PBR_MATERIALS__LIVE_VISUAL_AND_RUNTIME_GATES_REQUIRED__NOT_PROMOTED" if not fail else "FAIL__V039_NOT_A_PARENT","base":BASE,"map":MAP,"base_sha256":base_hash,"map_sha256":sha(MAP_FILE) if MAP_FILE.exists() else None,"slot_count":len(slots),"bindings":rows,"shell_collision_profile":str(c.get_collision_profile_name()),"promotion_authorized":False,"failures":fail}
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(p,indent=2),encoding="utf-8");print(json.dumps(p,indent=2))
if fail: raise RuntimeError("; ".join(fail))
unreal.SystemLibrary.quit_editor()
