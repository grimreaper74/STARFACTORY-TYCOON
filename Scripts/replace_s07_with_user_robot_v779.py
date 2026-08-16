from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, unreal

ROOT=Path(unreal.Paths.project_dir());BASE='/Game/LineBoss/Maps/LB_PressShop_Trains_InboundVisual_v770';TARGET='/Game/LineBoss/Maps/LB_PressShop_Trains_Inbound_UserS07_v779'
OUT=ROOT/'Saved/Audits/PressShopIntegration/s07_user_robot_placement_v779.json';PROTECTED=ROOT/'Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap';EXPECTED='5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8';DEST='/Game/LineBoss/Developer/Validation/PressTrains/S07UserRobotRuntime_v778'
lib=unreal.EditorAssetLibrary;levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);sha=lambda:hashlib.sha256(PROTECTED.read_bytes()).hexdigest().upper()
if sha()!=EXPECTED:raise RuntimeError('Protected v438 mismatch')
if OUT.exists() or lib.does_asset_exist(TARGET):raise RuntimeError('Refusing overwrite v779')
meshes=[]
for p in lib.list_assets(DEST,recursive=True,include_folder=False):
 a=unreal.load_asset(p)
 if isinstance(a,unreal.StaticMesh):meshes.append((p,a))
if len(meshes)!=6:raise RuntimeError(f'Expected 6 user robot meshes, got {len(meshes)}')
def role(path):
 n=path.upper()
 for r in ['BASE_STATIC','TURNTABLE','LOWER_ARM','UPPER_ARM','WRIST','VACUUM_TOOL']:
  if r in n:return r
 raise RuntimeError(f'Unknown role {path}')
items=sorted([(role(p),a,p) for p,a in meshes])
if not levels.new_level_from_template(TARGET,BASE):raise RuntimeError('Could not derive v779')

# Remove only the four temporary v756 orange robots; all presses, transfers,
# S01 cells, hall, inbound equipment and user-owned assets remain untouched.
removed=[]
for actor in list(actors.get_all_level_actors()):
 tags={str(t) for t in actor.tags};label=actor.get_actor_label()
 if 'LB.PressShop.S07Robots.v758' in tags or ('S07_UNLOAD_ROBOT_' in label and label.endswith('_v758')):
  removed.append(label)
  if not actors.destroy_actor(actor):raise RuntimeError(f'Could not remove temporary actor {label}')
if len(removed)!=36:raise RuntimeError(f'Expected 36 temporary S07 actors, removed {len(removed)}')

ys={'A':-4300,'B':-2100,'C':100,'D':2300};created=[];bounds={}
parents={'BASE_STATIC':'WORLD','TURNTABLE':'BASE_STATIC','LOWER_ARM':'TURNTABLE','UPPER_ARM':'LOWER_ARM','WRIST':'UPPER_ARM','VACUUM_TOOL':'WRIST'}
for train,y in ys.items():
 group=[]
 for r,mesh,p in items:
  actor=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(8600,y+420,0),unreal.Rotator())
  actor.set_actor_label(f'LB_TRAIN_{train}_S07_USER_ROBOT_{r}_v779')
  actor.tags=[unreal.Name(t) for t in [f'LB.PressTrain.Installed.TRAIN_{train}','LB.Station.S07.InspectUnload',f'LB.S07Robot.Component.{r}',f'LB.S07Robot.Parent.{parents[r]}','LB.PressShop.UserS07Robots.v779','LB.Source.UserMeshyRobot.v776','LB.Source.NoLegacyMapCopy']]
  c=actor.static_mesh_component;c.set_static_mesh(mesh);c.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS);movable=r!='BASE_STATIC';c.set_mobility(unreal.ComponentMobility.MOVABLE if movable else unreal.ComponentMobility.STATIC);c.set_editor_property('can_ever_affect_navigation',not movable)
  created.append(actor);group.append(actor)
 mins=[1e30]*3;maxs=[-1e30]*3
 for actor in group:
  o,e=actor.get_actor_bounds(False);vals=[o.x,o.y,o.z];ext=[e.x,e.y,e.z]
  for i in range(3):mins[i]=min(mins[i],vals[i]-ext[i]);maxs[i]=max(maxs[i],vals[i]+ext[i])
 bounds[train]={'min_cm':mins,'max_cm':maxs,'size_cm':[maxs[i]-mins[i] for i in range(3)]}

unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.save_current_level():raise RuntimeError('Save v779 failed')
fail=[]
if len(created)!=24:fail.append(f'created {len(created)} expected 24')
for t,b in bounds.items():
 if b['min_cm'][2]<-2:fail.append(f'{t} below floor {b["min_cm"][2]:.2f}')
 if not 350<b['size_cm'][2]<500:fail.append(f'{t} height unexpected {b["size_cm"][2]:.1f}')
if sha()!=EXPECTED:fail.append('protected hash changed')
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps({'revision':'v779','generated_utc':datetime.now(timezone.utc).isoformat(),'status':'PASS__TEMPORARY_S07_REPLACED_BY_USER_ROBOT_A_D__VISUAL_GATE_OPEN' if not fail else 'FAIL__V779','map':TARGET,'base':BASE,'removed_temporary_actor_count':len(removed),'created_actor_count':len(created),'components_per_robot':6,'robot_origin_cm':{'x':8600,'y_offset_from_train':420,'z':0},'kinematic_parent_contract':parents,'robot_bounds':bounds,'failures':fail,'protected_sha256':sha(),'legacy_robot_remaining':False,'meshy_credits_used_by_codex':0},indent=2),encoding='utf-8')
if fail:raise RuntimeError('; '.join(fail))
unreal.log('LINE_BOSS_S07_USER_ROBOT_PLACEMENT_V779_PASS')
