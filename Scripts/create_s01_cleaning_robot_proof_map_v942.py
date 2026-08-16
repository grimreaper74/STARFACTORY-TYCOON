from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,unreal

ROOT=Path(unreal.Paths.project_dir()); MAP='/Game/LineBoss/Developer/Validation/Maps/LB_S01_CleaningRobot_MaterialProof_v944'; BASE='/Game/LineBoss/Developer/Validation/BlenderApproved_v940'
PROTECTED=ROOT/'Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap'; EXPECTED='5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8'; OUT=ROOT/'Saved/Audits/PressShopIntegration/s01_cleaning_robot_proof_map_v942.json'
sha=lambda:hashlib.sha256(PROTECTED.read_bytes()).hexdigest().upper(); lib=unreal.EditorAssetLibrary; levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if sha()!=EXPECTED: raise RuntimeError('protected hash mismatch')
if lib.does_asset_exist(MAP): raise RuntimeError('refusing overwrite v944 proof map')
if not levels.new_level(MAP): raise RuntimeError('new proof level failed')
cube=unreal.load_asset('/Engine/BasicShapes/Cube.Cube'); floor=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(0,0,-25)); floor.set_actor_label('LB_PROOF_FLOOR_v942'); floor.static_mesh_component.set_static_mesh(cube); floor.set_actor_scale3d(unreal.Vector(12,12,.5))
sun=actors.spawn_actor_from_class(unreal.DirectionalLight,unreal.Vector(0,0,800),unreal.Rotator(-38,-35,0)); sun.set_actor_label('LB_PROOF_SUN_v942'); sun.get_component_by_class(unreal.DirectionalLightComponent).set_editor_property('intensity',6.0)
sky=actors.spawn_actor_from_class(unreal.SkyLight,unreal.Vector(0,0,500)); sky.set_actor_label('LB_PROOF_SKY_v942'); sky.get_component_by_class(unreal.SkyLightComponent).set_editor_property('intensity',1.3)
for loc,intensity,radius in [(unreal.Vector(-350,-500,650),9000,1200),(unreal.Vector(420,180,500),7000,1000)]:
 p=actors.spawn_actor_from_class(unreal.PointLight,loc); pc=p.get_component_by_class(unreal.PointLightComponent); pc.set_editor_property('intensity',intensity); pc.set_editor_property('attenuation_radius',radius)
s01=[]
for path in lib.list_assets(BASE+'/S01',recursive=True,include_folder=False):
 a=unreal.load_asset(path)
 if isinstance(a,unreal.StaticMesh):
  actor=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(0,160,0)); actor.set_actor_label('LB_PROOF_S01_'+a.get_name()); actor.static_mesh_component.set_static_mesh(a); s01.append(actor)
robot_paths=[p for p in lib.list_assets(BASE+'/CleaningRobot',recursive=True,include_folder=False) if isinstance(unreal.load_asset(p),unreal.StaticMesh)]
if len(robot_paths)!=1: raise RuntimeError(f'cleaning mesh resolution {robot_paths}')
robot=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(0,-470,0)); robot.set_actor_label('LB_PROOF_CLEANING_ROBOT_v942'); robot.static_mesh_component.set_static_mesh(unreal.load_asset(robot_paths[0]))
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.save_current_level(): raise RuntimeError('save proof map failed')
bounds={}
for label,group in [('S01',s01),('CLEANING_ROBOT',[robot])]:
 mins=[1e30]*3; maxs=[-1e30]*3
 for a in group:
  o,e=a.get_actor_bounds(False); ov=[o.x,o.y,o.z]; ev=[e.x,e.y,e.z]
  for i in range(3): mins[i]=min(mins[i],ov[i]-ev[i]); maxs[i]=max(maxs[i],ov[i]+ev[i])
 bounds[label]={'min_cm':mins,'max_cm':maxs,'size_cm':[maxs[i]-mins[i] for i in range(3)]}
fail=[]
if len(s01)!=52: fail.append(f'S01 actors {len(s01)}')
if sha()!=EXPECTED: fail.append('protected changed')
OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps({'revision':'v942','generated_utc':datetime.now(timezone.utc).isoformat(),'status':'PASS__ISOLATED_PROOF_MAP' if not fail else 'FAIL__V942','map':MAP,'s01_actor_count':len(s01),'cleaning_robot_actor_count':1,'bounds':bounds,'failures':fail,'protected_sha256':sha(),'game_map_modified':False,'meshy_credits_used_by_codex':0},indent=2),encoding='utf-8')
if fail: raise RuntimeError('; '.join(fail))
unreal.log('LINE_BOSS_S01_CLEANING_ROBOT_PROOF_MAP_V942_PASS')
