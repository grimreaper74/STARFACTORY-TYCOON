from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,unreal
ROOT=Path(unreal.Paths.project_dir());BASE='/Game/LineBoss/Maps/LB_PressShop_NewSegmentedTrains_Grounded_v750';TARGET='/Game/LineBoss/Maps/LB_PressShop_GroundedTrains_S07Robots_v758';OUT=ROOT/'Saved/Audits/PressShopIntegration/s07_unload_robot_placement_v758.json';PROTECTED=ROOT/'Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap';EXPECTED='5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8';DEST='/Game/LineBoss/Developer/Validation/PressTrains/S07UnloadRobotRuntime_v757'
lib=unreal.EditorAssetLibrary;levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);sha=lambda:hashlib.sha256(PROTECTED.read_bytes()).hexdigest().upper()
if sha()!=EXPECTED:raise RuntimeError('Protected v438 mismatch')
if OUT.exists() or lib.does_asset_exist(TARGET):raise RuntimeError('Refusing overwrite v758')
paths=[]
for p in lib.list_assets(DEST,recursive=True,include_folder=False):
 a=unreal.load_asset(p)
 if isinstance(a,unreal.StaticMesh):paths.append(p)
if len(paths)!=9:raise RuntimeError(f'Expected 9 robot meshes, got {len(paths)}')
def role(p):
 n=p.split('/')[-1].split('.')[0]
 for r in ['Base','Shoulder','UpperArm','Elbow','Forearm','Wrist','Gripper']:
  if r.lower() in n.lower():return r
 return 'VacuumCupNeg' if '-600' in n else 'VacuumCupPos'
items=sorted([(role(p),unreal.load_asset(p),p) for p in paths])
if not levels.new_level_from_template(TARGET,BASE):raise RuntimeError('Could not derive v758')
ys={'A':-4300,'B':-2100,'C':100,'D':2300};created=[];bounds={}
parents={'Base':'WORLD','Shoulder':'Base','UpperArm':'Shoulder','Elbow':'UpperArm','Forearm':'Elbow','Wrist':'Forearm','Gripper':'Wrist','VacuumCupNeg':'Gripper','VacuumCupPos':'Gripper'}
for train,y in ys.items():
 group=[]
 for r,mesh,p in items:
  a=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(8600,y+420,0),unreal.Rotator())
  a.set_actor_label(f'LB_TRAIN_{train}_S07_UNLOAD_ROBOT_{r}_v758');a.tags=[unreal.Name(t) for t in [f'LB.PressTrain.Installed.TRAIN_{train}','LB.Station.S07.InspectUnload',f'LB.S07Robot.Component.{r}',f'LB.S07Robot.Parent.{parents[r]}','LB.PressShop.S07Robots.v758','LB.Source.RuntimeRobot.v756','LB.Source.NoLegacyMapCopy']]
  c=a.static_mesh_component;c.set_static_mesh(mesh);c.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS);movable=r!='Base';c.set_mobility(unreal.ComponentMobility.MOVABLE if movable else unreal.ComponentMobility.STATIC);c.set_editor_property('can_ever_affect_navigation',not movable);created.append(a);group.append(a)
 mins=[1e30,1e30,1e30];maxs=[-1e30,-1e30,-1e30]
 for a in group:
  o,e=a.get_actor_bounds(False)
  for i,v in enumerate([o.x,o.y,o.z]):mins[i]=min(mins[i],v-[e.x,e.y,e.z][i]);maxs[i]=max(maxs[i],v+[e.x,e.y,e.z][i])
 bounds[train]={'min_cm':mins,'max_cm':maxs,'size_cm':[maxs[i]-mins[i] for i in range(3)]}
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.save_current_level():raise RuntimeError('Save v758 failed')
fail=[]
if len(created)!=36:fail.append(f'created {len(created)} expected 36')
for t,b in bounds.items():
 if b['min_cm'][2] < -2:fail.append(f'{t} below floor {b["min_cm"][2]:.2f}')
 if not 250<b['size_cm'][2]<400:fail.append(f'{t} height unexpected {b["size_cm"][2]:.1f}')
if sha()!=EXPECTED:fail.append('protected hash changed')
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps({'revision':'v758','generated_utc':datetime.now(timezone.utc).isoformat(),'status':'PASS__S07_ROBOTS_INSTALLED_A_D' if not fail else 'FAIL__V758','map':TARGET,'base':BASE,'robot_origin_cm':{'x':8600,'y_offset_from_train':420,'z':0},'created_actor_count':len(created),'components_per_robot':9,'kinematic_parent_contract':parents,'robot_bounds':bounds,'failures':fail,'protected_sha256':sha(),'meshy_credits_used':0},indent=2),encoding='utf-8')
if fail:raise RuntimeError('; '.join(fail))
unreal.log('LINE_BOSS_S07_ROBOT_PLACEMENT_V758_PASS')
