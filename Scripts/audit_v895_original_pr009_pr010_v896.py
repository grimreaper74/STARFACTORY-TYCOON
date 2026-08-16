from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,unreal
ROOT=Path(unreal.Paths.project_dir()).resolve();MAP='/Game/LineBoss/Maps/LB_PressShop_CleanConnectedS07_OriginalPR009_PR010_v20260809_v895';PROTECTED=ROOT/r'Content\LineBoss\Maps\LB_PressShop_BuilderAuthorityCandidate_v438.umap';EXPECTED='5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest().upper();before=sha(PROTECTED)
if before!=EXPECTED:raise RuntimeError('protected invariant')
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):raise RuntimeError(MAP)
expected={'LB_PR009_OriginalHighPoly_v895':([600,-2000,0],-90),'LB_PR010_OriginalHighPoly_v895':([1350,-2000,0],-90)};records=[]
for a in actors.get_all_level_actors():
 if a.get_actor_label() in expected:
  m=a.static_mesh_component.get_editor_property('static_mesh') if isinstance(a,unreal.StaticMeshActor) else None;loc=a.get_actor_location();records.append({'label':a.get_actor_label(),'location_cm':[loc.x,loc.y,loc.z],'yaw_deg':a.get_actor_rotation().yaw,'mesh':m.get_path_name() if m else None,'visible':a.static_mesh_component.get_editor_property('visible') if m else None})
if len(records)!=2:raise RuntimeError(f'persist audit {records}')
after=sha(PROTECTED)
if after!=before:raise RuntimeError('protected changed')
out=ROOT/r'Saved\Audits\PressShopIntegration\v895_original_pr009_pr010_reload_v896.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps({'generated_utc':datetime.now(timezone.utc).isoformat(),'status':'PASS_V791_CHILD_ACTORS_PERSISTED__VISUAL_REVIEW_REQUIRED__NOT_PROMOTED','map':MAP,'records':records,'protected_v438_before':before,'protected_v438_after':after},indent=2),encoding='utf-8');print(json.dumps(records,indent=2))
