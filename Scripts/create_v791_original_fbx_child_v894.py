"""Create a fresh v791 child and place PR009/PR010 originals at approved datums."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,unreal
ROOT=Path(unreal.Paths.project_dir()).resolve();SRC='/Game/LineBoss/Maps/LB_PressShop_CleanConnectedS07_v20260809_v791';MAP='/Game/LineBoss/Maps/LB_PressShop_CleanConnectedS07_OriginalPR009_PR010_v20260809_v895';PROTECTED=ROOT/r'Content\LineBoss\Maps\LB_PressShop_BuilderAuthorityCandidate_v438.umap';EXPECTED='5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest().upper();before=sha(PROTECTED)
if before!=EXPECTED:raise RuntimeError('protected invariant')
lib=unreal.EditorAssetLibrary;levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not lib.does_asset_exist(SRC) or lib.does_asset_exist(MAP):raise RuntimeError('source/fresh invariant')
if not lib.duplicate_asset(SRC,MAP):raise RuntimeError('duplicate v791')
specs={
 'PR009':{'loc':(600,-2000,0),'yaw':-90.0,'target':[520,760,425]},
 'PR010':{'loc':(1350,-2000,0),'yaw':-90.0,'target':[1400,840,360]},
}
records=[]
for station,s in specs.items():
 path=f'/Game/LineBoss/Candidates/PressShop/PR009_PR010_OriginalFBX_v884/{station}/SM_CA_MW_{station}_OriginalHighPoly_v883';mesh=lib.load_asset(path)
 if not isinstance(mesh,unreal.StaticMesh):raise RuntimeError(path)
 a=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(*s['loc']),unreal.Rotator(0,s['yaw'],0));a.set_actor_label(f'LB_{station}_OriginalHighPoly_v895');a.static_mesh_component.set_static_mesh(mesh);a.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION);a.tags=[unreal.Name(f'LB.Station.{station}'),unreal.Name('LB.Asset.NewApprovedCandidate'),unreal.Name('LB.Validation.v895')]
 d=mesh.get_bounds().box_extent*2;ifail=max(abs(v-e) for v,e in zip((d.x,d.y,d.z),s['target']))
 if ifail>=2:raise RuntimeError(f'{station} bounds')
 records.append({'station':station,'label':a.get_actor_label(),'location_cm':list(s['loc']),'yaw_deg':s['yaw'],'mesh':mesh.get_path_name(),'mesh_bounds_cm':[d.x,d.y,d.z]})
if not levels.save_current_level():raise RuntimeError('save v895')
after=sha(PROTECTED)
if after!=before:raise RuntimeError('protected changed')
map_file=ROOT/r'Content\LineBoss\Maps\LB_PressShop_CleanConnectedS07_OriginalPR009_PR010_v20260809_v895.umap'
if not map_file.exists():raise RuntimeError('v895 file missing')
out=ROOT/r'Saved\Audits\PressShopIntegration\v791_original_pr009_pr010_child_v895.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps({'generated_utc':datetime.now(timezone.utc).isoformat(),'status':'PASS_V791_CHILD_CREATED_AND_SAVED__SEPARATE_RELOAD_AUDIT_REQUIRED__NOT_PROMOTED','source_map':SRC,'map':MAP,'map_sha256':sha(map_file),'records':records,'protected_v438_before':before,'protected_v438_after':after,'meshy_credits_used':0},indent=2),encoding='utf-8');unreal.log('LINE_BOSS_V791_ORIGINAL_PR009_PR010_CHILD_V895_PASS')
