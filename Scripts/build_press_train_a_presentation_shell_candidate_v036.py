"""Fresh v034 child using the proven v035 import with explicit metres-to-cm scale."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()); BASE="/Game/LineBoss/Maps/LB_PressTrainAFabricationCollisionSafeCandidate_v034"; MAP="/Game/LineBoss/Maps/LB_PressTrainAPresentationShellCandidate_v036"; ASSET="/Game/LineBoss/Candidates/PressTrains/TrainA/PresentationShell_v035/SM_CA_MW_PTA_PresentationShell_v014"
BASE_FILE=ROOT/"Content/LineBoss/Maps/LB_PressTrainAFabricationCollisionSafeCandidate_v034.umap"; MAP_FILE=ROOT/"Content/LineBoss/Maps/LB_PressTrainAPresentationShellCandidate_v036.umap"; OUT=ROOT/"Saved/Audits/PressTrains/press_train_a_presentation_shell_build_v036.json"
lib=unreal.EditorAssetLibrary; levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); api=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
 return h.hexdigest().upper()
if lib.does_asset_exist(MAP) or OUT.exists(): raise RuntimeError("refusing to overwrite v036")
base_hash=sha(BASE_FILE); mesh=lib.load_asset(ASSET)
if not isinstance(mesh,unreal.StaticMesh): raise RuntimeError("retained v035 import missing")
if not levels.new_level_from_template(MAP,BASE): raise RuntimeError("fresh v034 child failed")
a=api.spawn_actor_from_object(mesh,unreal.Vector(0,0,0),unreal.Rotator(0,0,0),False); a.set_actor_label("CA_MW_PTA_PresentationShell_v014_FIXED_CM")
a.set_actor_scale3d(unreal.Vector(100,100,100)); a.tags=[unreal.Name(x) for x in ("LB.PressTrain.PresentationShell.v014","LB.PressTrain.TrainA","LB.Asset.Candidate.v036","LB.Asset.CandidateNotPromoted","LB.Collision.NoCollision")]
c=a.static_mesh_component; c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION); c.set_editor_property("can_ever_affect_navigation",False); c.set_editor_property("cast_shadow",True)
actors=api.get_all_level_actors(); train=[x for x in actors if isinstance(x,unreal.StaticMeshActor) and "LB.PressTrain.ProcessDirection.PositiveY" in {str(t) for t in x.tags}]; stations=[x for x in actors if x.get_class().get_name()=="LBPressTrainAStation"]
b=mesh.get_bounds(); installed=[float(b.box_extent.x*200),float(b.box_extent.y*200),float(b.box_extent.z*200)]; fail=[]
if len(train)!=336: fail.append(f"retained train actors {len(train)} != 336")
if len(stations)!=1: fail.append(f"station count {len(stations)} != 1")
if c.get_collision_enabled()!=unreal.CollisionEnabled.NO_COLLISION: fail.append(f"shell collision is {c.get_collision_enabled()}")
if c.get_editor_property("can_ever_affect_navigation"): fail.append("shell affects navigation")
if not (1000<installed[2]<1100 and 3500<installed[1]<3700 and 105<installed[0]<125): fail.append(f"installed shell bounds unexpected {installed}")
if not levels.save_current_level(): fail.append("save failed")
if sha(BASE_FILE)!=base_hash: fail.append("protected v034 changed")
p={"status":"PASS__V014_SHELL_CORRECTED_CM_SCALE_IN_FRESH_V034_CHILD__LIVE_VISUAL_AND_RUNTIME_GATES_REQUIRED__NOT_PROMOTED" if not fail else "FAIL__V036_NOT_A_PARENT","base":BASE,"map":MAP,"base_sha256":base_hash,"map_sha256":sha(MAP_FILE) if MAP_FILE.exists() else None,"shell_asset":ASSET,"actor_scale":[100,100,100],"installed_shell_bounds_cm":installed,"shell_collision":str(c.get_collision_enabled()),"shell_affects_navigation":False,"retained_train_actor_count":len(train),"native_station_count":len(stations),"promotion_authorized":False,"failures":fail}
OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(p,indent=2),encoding="utf-8"); print(json.dumps(p,indent=2))
if fail: raise RuntimeError("; ".join(fail))
unreal.SystemLibrary.quit_editor()
