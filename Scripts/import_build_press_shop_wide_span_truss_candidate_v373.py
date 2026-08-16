"""Fresh v367 structural-visual child with 40 m trussed bays at X=2/6 km."""
from datetime import datetime, timezone
import hashlib, json
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir())
SOURCE=ROOT/"SourceAssets/Candidate/PressShop/Structure/WideSpanTruss_v372/FBX/SM_CA_MW_PressShop_WideSpanTruss_40m_TBC_v372.fbx"
SOURCE_SHA="D437D415B4313900D1FA05D6502921E7D699E9187068472906267CB73D92FF67"
BASE="/Game/LineBoss/Maps/LB_PressShop_ExpandedTrainNavOptimizedCandidate_v367"
BASE_FILE=ROOT/"Content/LineBoss/Maps/LB_PressShop_ExpandedTrainNavOptimizedCandidate_v367.umap"
BASE_SHA="5CF44DDD90C49BAD1447C50406680045862A957ED01FD4BBF44C58C685594355"
MAP="/Game/LineBoss/Maps/LB_PressShop_WideSpanTrussCandidate_v373"
MAP_FILE=ROOT/"Content/LineBoss/Maps/LB_PressShop_WideSpanTrussCandidate_v373.umap"
DEST="/Game/LineBoss/Candidates/PressShop/Structure/WideSpanTruss_v373"
ASSET=DEST+"/SM_CA_MW_PressShop_WideSpanTruss_40m_TBC_v372"
OUT=ROOT/"Saved/Audits/PressShopIntegration/press_shop_wide_span_truss_build_v373.json"
Y_ROWS=(-5250,-3750,-2250,-750,750,2250)

def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as s:
  for chunk in iter(lambda:s.read(1048576),b''):h.update(chunk)
 return h.hexdigest().upper()

lib=unreal.EditorAssetLibrary;levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if sha(SOURCE)!=SOURCE_SHA or sha(BASE_FILE)!=BASE_SHA:raise RuntimeError("source/base hash drift")
if lib.does_directory_exist(DEST) or lib.does_asset_exist(MAP) or OUT.exists():raise RuntimeError("refusing to overwrite v373")
task=unreal.AssetImportTask();task.set_editor_properties({"filename":str(SOURCE),"destination_path":DEST,"destination_name":"SM_CA_MW_PressShop_WideSpanTruss_40m_TBC_v372","automated":True,"replace_existing":False,"save":True})
options=unreal.FbxImportUI();options.set_editor_properties({"import_mesh":True,"import_as_skeletal":False,"import_materials":True,"import_textures":False,"mesh_type_to_import":unreal.FBXImportType.FBXIT_STATIC_MESH})
data=options.get_editor_property("static_mesh_import_data");data.set_editor_properties({"combine_meshes":True,"convert_scene":True,"convert_scene_unit":True,"transform_vertex_to_absolute":False,"bake_pivot_in_vertex":False,"generate_lightmap_u_vs":True,"auto_generate_collision":False,"remove_degenerates":True})
task.set_editor_property("options",options);unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
mesh=lib.load_asset(ASSET)
if not isinstance(mesh,unreal.StaticMesh):raise RuntimeError("truss import missing")
if not levels.new_level_from_template(MAP,BASE):raise RuntimeError("fresh v367 child failed")
by_label={a.get_actor_label():a for a in actors.get_all_level_actors()}
removed_columns=[]
for y in Y_ROWS:
 label=f"LB_PRESS_Column_2000_{y}"
 actor=by_label.get(label)
 if actor is None:raise RuntimeError(f"missing column {label}")
 comp=actor.get_component_by_class(unreal.StaticMeshComponent)
 if comp is None or comp.get_collision_enabled()==unreal.CollisionEnabled.NO_COLLISION:raise RuntimeError(f"column authority unexpected {label}")
 removed_columns.append(label);actors.destroy_actor(actor)
removed_old_girders=[]
for actor in list(actors.get_all_level_actors()):
 if actor.get_actor_label().startswith("LB_V301_WIDESPAN_TRANSFER_GIRDER_"):
  removed_old_girders.append(actor.get_actor_label());actors.destroy_actor(actor)
if len(removed_old_girders)!=6:raise RuntimeError(f"old girder count {len(removed_old_girders)}")
trusses=[]
for x in (2000.0,6000.0):
 for y in Y_ROWS:
  actor=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(x,float(y),1740.0),unreal.Rotator())
  actor.static_mesh_component.set_static_mesh(mesh);actor.set_actor_scale3d(unreal.Vector(100,100,100))
  actor.set_actor_label(f"LB_V373_WIDESPAN_TRUSS_X{int(x)}_Y{y:+05d}_TBC")
  comp=actor.static_mesh_component;comp.set_collision_profile_name("NoCollision");comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION);comp.set_editor_property("can_ever_affect_navigation",False);comp.set_editor_property("generate_overlap_events",False)
  actor.tags=[unreal.Name(v) for v in ("LB.Structure.WideSpanTransferTruss.TBC","LB.Asset.Candidate.v373","LB.Asset.CandidateNotPromoted","LB.PresentationOnly.NoEngineeringAuthority","LB.Collision.NoCollision.VisualOnly","LB.Navigation.None")]
  origin,extent=actor.get_actor_bounds(False);size=[extent.x*2,extent.y*2,extent.z*2]
  if not(3950<=size[0]<=4050 and 40<=size[1]<=70 and 95<=size[2]<=130):raise RuntimeError(f"truss bounds {size}")
  trusses.append({"label":actor.get_actor_label(),"origin_cm":list(origin.to_tuple()),"size_cm":size})
train_counts={k:sum(1 for a in actors.get_all_level_actors() if f"LB.PressTrain.Installed.TRAIN_{k}" in {str(t) for t in a.tags}) for k in 'ABCD'}
failures=[]
if train_counts!={"A":338,"B":338,"C":338,"D":338}:failures.append(f"train counts {train_counts}")
if len(removed_columns)!=6 or len(trusses)!=12:failures.append("structural counts")
if not levels.save_current_level():failures.append("save failed")
if sha(BASE_FILE)!=BASE_SHA:failures.append("protected v367 hash drift")
payload={"$schema":"cairnwell/audit/press-shop-wide-span-truss-build-v373/v1","generated_utc":datetime.now(timezone.utc).isoformat(),"status":"PASS__FRESH_40M_TRUSSED_BAY_VISUAL_SUCCESSOR__ALL_VISUAL_AND_RUNTIME_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__NOT_RETAINED","base":BASE,"base_sha256":BASE_SHA,"map":MAP,"map_sha256":sha(MAP_FILE) if MAP_FILE.exists() else None,"source_fbx_sha256":SOURCE_SHA,"removed_x2000_columns":removed_columns,"removed_v301_crude_girders":removed_old_girders,"added_tbc_visual_trusses":trusses,"structural_engineering_status":"TBC_PRESENTATION_ONLY","train_counts":train_counts,"collision_policy":"trusses NoCollision; six x2000 column blockers absent only in fresh child","promotion_authorized":False,"failures":failures}
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,indent=2)+"\n",encoding='utf-8');print(json.dumps(payload,indent=2))
if failures:raise RuntimeError('; '.join(failures))
unreal.SystemLibrary.quit_editor()
