"""Place already imported originals into the explicit isolated level and prove persistence."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,unreal
ROOT=Path(unreal.Paths.project_dir()).resolve();MAP='/Game/LineBoss/Maps/LB_PressShop_PR009_PR010_OriginalFBX_Isolated_v884';PROTECTED=ROOT/r'Content\LineBoss\Maps\LB_PressShop_BuilderAuthorityCandidate_v438.umap';EXPECTED='5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest().upper();before=sha(PROTECTED)
if before!=EXPECTED:raise RuntimeError('protected invariant')
lib=unreal.EditorAssetLibrary;levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):raise RuntimeError('load isolated map')
for a in actors.get_all_level_actors():
 if a.get_actor_label() in ('LB_PR009_OriginalHighPoly_v892','LB_PR010_OriginalHighPoly_v892'):actors.destroy_actor(a)
records=[]
for station,loc in {'PR009':(-650,0,0),'PR010':(650,0,0)}.items():
 path=f'/Game/LineBoss/Candidates/PressShop/PR009_PR010_OriginalFBX_v884/{station}/SM_CA_MW_{station}_OriginalHighPoly_v883';mesh=lib.load_asset(path)
 if not isinstance(mesh,unreal.StaticMesh):raise RuntimeError(path)
 a=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(*loc),unreal.Rotator());a.set_actor_label(f'LB_{station}_OriginalHighPoly_v892');a.static_mesh_component.set_static_mesh(mesh);a.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION);a.tags=[unreal.Name(f'LB.Station.{station}'),unreal.Name('LB.IsolatedValidation.v892')]
 d=mesh.get_bounds().box_extent*2;records.append({'station':station,'label':a.get_actor_label(),'location':[a.get_actor_location().x,a.get_actor_location().y,a.get_actor_location().z],'mesh':mesh.get_path_name(),'bounds_cm':[d.x,d.y,d.z]})
if not levels.save_current_level():raise RuntimeError('save explicit isolated map')
# Reload and prove persistence rather than trusting the spawn call.
if not levels.load_level(MAP):raise RuntimeError('reload isolated map')
persisted=[]
for a in actors.get_all_level_actors():
 if a.get_actor_label() in [r['label'] for r in records]:
  m=a.static_mesh_component.get_editor_property('static_mesh') if isinstance(a,unreal.StaticMeshActor) else None;persisted.append({'label':a.get_actor_label(),'location':[a.get_actor_location().x,a.get_actor_location().y,a.get_actor_location().z],'mesh':m.get_path_name() if m else None})
if len(persisted)!=2:raise RuntimeError(f'placement did not persist: {persisted}')
after=sha(PROTECTED)
if after!=before:raise RuntimeError('protected changed')
out=ROOT/r'Saved\Audits\PressShopIntegration\pr009_pr010_isolated_placement_v892.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps({'generated_utc':datetime.now(timezone.utc).isoformat(),'status':'PASS_EXPLICIT_PLACEMENT_PERSISTED__VISUAL_REVIEW_REQUIRED','map':MAP,'records':records,'persisted_after_reload':persisted,'protected_v438_before':before,'protected_v438_after':after},indent=2),encoding='utf-8');unreal.log('LINE_BOSS_PR009_PR010_PLACEMENT_V892_PASS')
