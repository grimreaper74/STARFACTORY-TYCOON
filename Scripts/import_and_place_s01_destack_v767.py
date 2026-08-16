from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,unreal
ROOT=Path(unreal.Paths.project_dir());SOURCE=Path(r'C:\Users\greg_\Projects\LineBoss_Workspace\SourceAssets\Candidate\PressTrains\Shared\S01DestackRuntime_v760\Cairnwell_S01_Destack_Runtime_v760.glb');DEST='/Game/LineBoss/Developer/Validation/PressTrains/S01DestackRuntime_v766';BASE='/Game/LineBoss/Maps/LB_PressShop_Trains_Oriented_S07Robots_v763';TARGET='/Game/LineBoss/Maps/LB_PressShop_Trains_S01_S07_v767';INTAKE=ROOT/'Saved/Audits/PressShopIntegration/s01_destack_intake_v766.json';OUT=ROOT/'Saved/Audits/PressShopIntegration/s01_destack_placement_v767.json';PROTECTED=ROOT/'Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap';EXPECTED='5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8'
lib=unreal.EditorAssetLibrary;levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);sha=lambda:hashlib.sha256(PROTECTED.read_bytes()).hexdigest().upper()
if sha()!=EXPECTED:raise RuntimeError('Protected v438 mismatch')
if INTAKE.exists() or OUT.exists() or lib.does_asset_exist(TARGET) or (lib.does_directory_exist(DEST) and lib.list_assets(DEST,recursive=True,include_folder=False)):raise RuntimeError('Refusing overwrite v766/v767')
t=unreal.AssetImportTask();t.set_editor_properties({'filename':str(SOURCE),'destination_path':DEST,'automated':True,'replace_existing':False,'replace_existing_settings':False,'save':True});unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t]);unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
paths=[]
for p in lib.list_assets(DEST,recursive=True,include_folder=False):
 a=unreal.load_asset(p)
 if isinstance(a,unreal.StaticMesh):paths.append(p)
roles=['STATIC_FRAME','LIFT_TABLE','BLANK_STACK','PICK_HEAD','FEED_ROLLERS'];items=[];fail=[]
for r in roles:
 hits=[p for p in paths if r.lower() in p.lower()]
 if len(hits)!=1:fail.append(f'{r} resolved {hits}')
 else:items.append((r,unreal.load_asset(hits[0])))
if len(paths)!=5:fail.append(f'mesh count {len(paths)} expected 5')
INTAKE.parent.mkdir(parents=True,exist_ok=True);INTAKE.write_text(json.dumps({'revision':'v766','generated_utc':datetime.now(timezone.utc).isoformat(),'status':'PASS__S01_FIVE_COMPONENT_INTAKE' if not fail else 'FAIL__V766','source':str(SOURCE),'destination':DEST,'static_meshes':paths,'failures':fail,'protected_sha256':sha(),'meshy_credits_used':0},indent=2),encoding='utf-8')
if fail:raise RuntimeError('; '.join(fail))
if not levels.new_level_from_template(TARGET,BASE):raise RuntimeError('Could not derive v767')
old=[a for a in actors.get_all_level_actors() if a.get_actor_label().startswith('LB_NEW_TRAIN_') and '_INFEED_ROLLER_CONVEYOR' in a.get_actor_label()]
if len(old)!=4:raise RuntimeError(f'Expected 4 old infeed conveyors, got {len(old)}')
actors.destroy_actors(old);ys={'A':-4300,'B':-2100,'C':100,'D':2300};created=[];bounds={}
for train,y in ys.items():
 group=[]
 for role,mesh in items:
  a=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(-820,y,0),unreal.Rotator(0,0,-90));a.set_actor_label(f'LB_TRAIN_{train}_S01_DESTACK_{role}_v767');a.tags=[unreal.Name(t) for t in [f'LB.PressTrain.Installed.TRAIN_{train}','LB.Station.S01.DestackBlankFeed',f'LB.S01.Component.{role}','LB.PressShop.S01Destack.v767','LB.Source.DedicatedEndCells.v027','LB.Source.NoLegacyMapCopy']];c=a.static_mesh_component;c.set_static_mesh(mesh);c.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS);movable=role!='STATIC_FRAME';c.set_mobility(unreal.ComponentMobility.MOVABLE if movable else unreal.ComponentMobility.STATIC);c.set_editor_property('can_ever_affect_navigation',not movable);created.append(a);group.append(a)
 mins=[1e30]*3;maxs=[-1e30]*3
 for a in group:
  o,e=a.get_actor_bounds(False);ov=[o.x,o.y,o.z];ev=[e.x,e.y,e.z]
  for i in range(3):mins[i]=min(mins[i],ov[i]-ev[i]);maxs[i]=max(maxs[i],ov[i]+ev[i])
 bounds[train]={'min_cm':mins,'max_cm':maxs,'size_cm':[maxs[i]-mins[i] for i in range(3)]}
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.save_current_level():raise RuntimeError('Save v767 failed')
fail=[]
if len(created)!=20:fail.append(f'created {len(created)} expected 20')
for t,b in bounds.items():
 if b['min_cm'][2]<-2:fail.append(f'{t} below floor')
 if b['max_cm'][0]>-270:fail.append(f'{t} overlaps S02 envelope maxX {b["max_cm"][0]:.1f}')
if sha()!=EXPECTED:fail.append('protected hash changed')
OUT.write_text(json.dumps({'revision':'v767','generated_utc':datetime.now(timezone.utc).isoformat(),'status':'PASS__S01_DESTACK_INSTALLED_A_D' if not fail else 'FAIL__V767','map':TARGET,'base':BASE,'removed_provisional_infeed_conveyors':len(old),'created_actor_count':len(created),'components_per_cell':5,'cell_origin_cm':[-820,'TRAIN_Y',0],'yaw_deg':-90,'bounds':bounds,'failures':fail,'protected_sha256':sha(),'meshy_credits_used':0},indent=2),encoding='utf-8')
if fail:raise RuntimeError('; '.join(fail))
unreal.log('LINE_BOSS_S01_DESTACK_V767_PASS')
