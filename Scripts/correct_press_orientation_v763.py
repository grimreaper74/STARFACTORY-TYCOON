from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,unreal
ROOT=Path(unreal.Paths.project_dir());BASE='/Game/LineBoss/Maps/LB_PressShop_GroundedTrains_S07Robots_v758';TARGET='/Game/LineBoss/Maps/LB_PressShop_Trains_Oriented_S07Robots_v763';OUT=ROOT/'Saved/Audits/PressShopIntegration/press_orientation_correction_v763.json';PROTECTED=ROOT/'Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap';EXPECTED='5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8'
lib=unreal.EditorAssetLibrary;levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);sha=lambda:hashlib.sha256(PROTECTED.read_bytes()).hexdigest().upper()
if sha()!=EXPECTED:raise RuntimeError('Protected v438 mismatch')
if OUT.exists() or lib.does_asset_exist(TARGET):raise RuntimeError('Refusing overwrite v763')
if not levels.new_level_from_template(TARGET,BASE):raise RuntimeError('Could not derive v763')
changed=[]
for a in actors.get_all_level_actors():
 tags={str(t) for t in a.tags};stations=[t for t in tags if t.startswith('LB.PressTrain.Station.S')]
 if stations and 'LB.PressShop.Grounded.v750' in tags:
  before=a.get_actor_rotation();a.set_actor_rotation(unreal.Rotator(0,0,-90),False);a.tags=list(a.tags)+[unreal.Name('LB.PressOrientation.AuthorityYawMinus90.v763')];changed.append({'label':a.get_actor_label(),'station':stations[0],'before_yaw':before.yaw,'after_yaw':a.get_actor_rotation().yaw})
if len(changed)!=120:raise RuntimeError(f'Expected 120 press components, got {len(changed)}')
if not levels.save_current_level():raise RuntimeError('Save v763 failed')
fail=[]
if any(abs(r['after_yaw']+90)>0.01 for r in changed):fail.append('not all press components yaw -90')
if sha()!=EXPECTED:fail.append('protected hash changed')
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps({'revision':'v763','generated_utc':datetime.now(timezone.utc).isoformat(),'status':'PASS__PRESS_CELLS_MATCH_RETAINED_MINUS90_YAW' if not fail else 'FAIL__V763','map':TARGET,'base':BASE,'retained_authority_yaw_deg':-90,'corrected_actor_count':len(changed),'changed':changed,'unchanged_scope':['segmented transfers','infeed/outfeed conveyors','S07 robots','hall architecture'],'failures':fail,'protected_sha256':sha(),'meshy_credits_used':0},indent=2),encoding='utf-8')
if fail:raise RuntimeError('; '.join(fail))
unreal.log('LINE_BOSS_PRESS_ORIENTATION_V763_PASS')
