"""Fresh v367 child using the measured-complete v373 truss import."""
from datetime import datetime, timezone
import hashlib,json
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir());BASE="/Game/LineBoss/Maps/LB_PressShop_ExpandedTrainNavOptimizedCandidate_v367";BASE_FILE=ROOT/"Content/LineBoss/Maps/LB_PressShop_ExpandedTrainNavOptimizedCandidate_v367.umap";BASE_SHA="5CF44DDD90C49BAD1447C50406680045862A957ED01FD4BBF44C58C685594355"
MAP="/Game/LineBoss/Maps/LB_PressShop_WideSpanTrussCandidate_v374";MAP_FILE=ROOT/"Content/LineBoss/Maps/LB_PressShop_WideSpanTrussCandidate_v374.umap";ASSET="/Game/LineBoss/Candidates/PressShop/Structure/WideSpanTruss_v373/SM_CA_MW_PressShop_WideSpanTruss_40m_TBC_v372";OUT=ROOT/"Saved/Audits/PressShopIntegration/press_shop_wide_span_truss_build_v374.json";Y_ROWS=(-5250,-3750,-2250,-750,750,2250)
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as s:
  for c in iter(lambda:s.read(1048576),b''):h.update(c)
 return h.hexdigest().upper()
lib=unreal.EditorAssetLibrary;levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if sha(BASE_FILE)!=BASE_SHA:raise RuntimeError('base drift')
if lib.does_asset_exist(MAP) or OUT.exists():raise RuntimeError('refusing overwrite v374')
mesh=lib.load_asset(ASSET)
if not isinstance(mesh,unreal.StaticMesh):raise RuntimeError('retained truss import missing')
if not levels.new_level_from_template(MAP,BASE):raise RuntimeError('fresh child failed')
by_label={a.get_actor_label():a for a in actors.get_all_level_actors()};removed=[]
for y in Y_ROWS:
 label=f"LB_PRESS_Column_2000_{y}";actor=by_label.get(label)
 if actor is None:raise RuntimeError(f'missing {label}')
 comp=actor.get_component_by_class(unreal.StaticMeshComponent)
 if comp is None or comp.get_collision_enabled()==unreal.CollisionEnabled.NO_COLLISION:raise RuntimeError(f'bad column {label}')
 removed.append(label);actors.destroy_actor(actor)
old=[]
for actor in list(actors.get_all_level_actors()):
 if actor.get_actor_label().startswith('LB_V301_WIDESPAN_TRANSFER_GIRDER_'):old.append(actor.get_actor_label());actors.destroy_actor(actor)
if len(old)!=6:raise RuntimeError(f'old girder count {len(old)}')
trusses=[]
for x in (2000.0,6000.0):
 for y in Y_ROWS:
  actor=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(x,float(y),1740),unreal.Rotator());actor.static_mesh_component.set_static_mesh(mesh);actor.set_actor_scale3d(unreal.Vector(100,100,100));actor.set_actor_label(f"LB_V374_WIDESPAN_TRUSS_X{int(x)}_Y{y:+05d}_TBC")
  comp=actor.static_mesh_component;comp.set_collision_profile_name('NoCollision');comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION);comp.set_editor_property('can_ever_affect_navigation',False);comp.set_editor_property('generate_overlap_events',False)
  actor.tags=[unreal.Name(v) for v in ('LB.Structure.WideSpanTransferTruss.TBC','LB.Asset.Candidate.v374','LB.Asset.CandidateNotPromoted','LB.PresentationOnly.NoEngineeringAuthority','LB.Collision.NoCollision.VisualOnly','LB.Navigation.None')]
  origin,extent=actor.get_actor_bounds(False);size=[extent.x*2,extent.y*2,extent.z*2]
  if not(4000<=size[0]<=4020 and 70<=size[1]<=74 and 120<=size[2]<=124):raise RuntimeError(f'truss bounds {size}')
  trusses.append({'label':actor.get_actor_label(),'origin_cm':list(origin.to_tuple()),'size_cm':size})
train_counts={k:sum(1 for a in actors.get_all_level_actors() if f'LB.PressTrain.Installed.TRAIN_{k}' in {str(t) for t in a.tags}) for k in 'ABCD'};fail=[]
if train_counts!={'A':338,'B':338,'C':338,'D':338}:fail.append(f'train counts {train_counts}')
if not levels.save_current_level():fail.append('save failed')
if sha(BASE_FILE)!=BASE_SHA:fail.append('base changed')
payload={'$schema':'cairnwell/audit/press-shop-wide-span-truss-build-v374/v1','generated_utc':datetime.now(timezone.utc).isoformat(),'status':'PASS__FRESH_40M_TRUSSED_BAY_VISUAL_SUCCESSOR__VISUAL_AND_RUNTIME_GATES_REQUIRED__NOT_PROMOTED' if not fail else 'FAIL__NOT_RETAINED','base':BASE,'base_sha256':BASE_SHA,'map':MAP,'map_sha256':sha(MAP_FILE) if MAP_FILE.exists() else None,'truss_asset':ASSET,'rejected_predecessor':'v373 failed only its too-tight 70 cm width tolerance; never parent from its partial map','removed_x2000_columns':removed,'removed_v301_crude_girders':old,'added_tbc_visual_trusses':trusses,'structural_engineering_status':'TBC_PRESENTATION_ONLY','train_counts':train_counts,'promotion_authorized':False,'failures':fail}
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8');print(json.dumps(payload,indent=2))
if fail:raise RuntimeError('; '.join(fail))
unreal.SystemLibrary.quit_editor()
