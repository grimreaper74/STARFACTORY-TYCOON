"""Replace v013 diagnostic FBX modules with textured GLB authorities and correct press orientation."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,unreal
ROOT=Path(unreal.Paths.project_dir()).resolve();SOURCE='/Game/LineBoss/Maps/LB_PressShop_CleanApprovedTrainsPaint_v20260809_v013';MAP='/Game/LineBoss/Maps/LB_PressShop_CleanApprovedTrainsPaint_v20260809_v015'
SRC_DIR=Path(r'C:\Users\greg_\Projects\LineBoss_Workspace\SourceAssets\Candidate\PressTrains\TrainA\NewApprovedAssembly_v20260809_v005\RuntimeTexturedModules_v015');DEST='/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v015/TexturedModules'
OUT=ROOT/r'Saved\Audits\PressShopIntegration\clean_approved_trains_textured_oriented_v20260809_v015.json';P=ROOT/r'Content\LineBoss\Maps\LB_PressShop_BuilderAuthorityCandidate_v438.umap';E='5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8'
lib=unreal.EditorAssetLibrary;levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest().upper();before=sha(P)
if before!=E or lib.does_asset_exist(MAP) or OUT.exists():raise RuntimeError('fresh/protected invariant')
files={'station':'SM_CA_MW_PressStation_S02_S06_Textured_v015.glb','roller':'SM_CA_MW_InterstageRoller_Textured_v015.glb','s01':'SM_CA_MW_S01_Destack_Textured_v015.glb','s07':'SM_CA_MW_S07_UnloadRobot_Static_Textured_v015.glb'}
meshes={};inventories={}
for key,filename in files.items():
 src=SRC_DIR/filename
 if not src.is_file():raise RuntimeError(src)
 d=f'{DEST}/{key.capitalize()}'
 t=unreal.AssetImportTask();t.set_editor_properties({'filename':str(src),'destination_path':d,'automated':True,'replace_existing':False,'save':True});unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t]);unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
 inventory=[]
 for ap in lib.list_assets(d,recursive=True,include_folder=False):
  a=lib.load_asset(ap);inventory.append({'path':ap,'class':a.get_class().get_name() if a else None})
  if isinstance(a,unreal.StaticMesh):meshes[key]=a
 inventories[key]=inventory
if set(meshes)!=set(files):raise RuntimeError(f'missing meshes {meshes}')
if not levels.new_level_from_template(MAP,SOURCE):raise RuntimeError('map child')
counts={k:0 for k in files}
for a in actors.get_all_level_actors():
 label=a.get_actor_label()
 if not isinstance(a,unreal.StaticMeshActor):continue
 if '_S0' in label and '_Press' in label:
  a.static_mesh_component.set_static_mesh(meshes['station']);r=a.get_actor_rotation();a.set_actor_rotation(unreal.Rotator(r.pitch,r.yaw+90,r.roll),False);a.set_actor_scale3d(unreal.Vector(1,1,1));counts['station']+=1
 elif '_Roller_' in label or '_S07_DischargeRoller' in label:
  a.static_mesh_component.set_static_mesh(meshes['roller']);a.set_actor_scale3d(unreal.Vector(1,1,1));counts['roller']+=1
 elif '_S01_Destack' in label:
  a.static_mesh_component.set_static_mesh(meshes['s01']);a.set_actor_scale3d(unreal.Vector(1,1,1));counts['s01']+=1
 elif '_S07_UnloadRobot' in label:
  a.static_mesh_component.set_static_mesh(meshes['s07']);a.set_actor_scale3d(unreal.Vector(1,1,1));counts['s07']+=1
if counts!={'station':20,'roller':28,'s01':4,'s07':4}:raise RuntimeError(counts)
if not levels.save_current_level():raise RuntimeError('save')
after=sha(P)
if after!=before:raise RuntimeError('protected changed')
mf=ROOT/r'Content\LineBoss\Maps\LB_PressShop_CleanApprovedTrainsPaint_v20260809_v015.umap';bounds={k:[(m.get_bounds().box_extent*2).x,(m.get_bounds().box_extent*2).y,(m.get_bounds().box_extent*2).z] for k,m in meshes.items()}
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps({'status':'PASS_REPLACEMENT__TEXTURED_GLB_AUTHORITIES__PRESS_FRONT_ROTATED_TO_OPERATOR_AISLE__VISUAL_REVIEW_REQUIRED__NOT_PROMOTED','generated_utc':datetime.now(timezone.utc).isoformat(),'source':SOURCE,'map':MAP,'map_sha256':sha(mf),'module_assets':{k:v.get_path_name() for k,v in meshes.items()},'module_bounds_cm':bounds,'replacement_counts':counts,'press_yaw_correction_deg':90,'inventories':inventories,'v013_status':'REJECTED_DIAGNOSTIC_ONLY__FBX_GREY_AND_SIDEWAYS','meshy_credits_used':0,'protected_v438_before':before,'protected_v438_after':after},indent=2),encoding='utf-8');unreal.log('LINE_BOSS_CLEAN_TEXTURED_ORIENTED_MODULES_V015_PASS')
