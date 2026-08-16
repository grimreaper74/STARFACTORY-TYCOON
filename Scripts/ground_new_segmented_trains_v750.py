from pathlib import Path
from datetime import datetime, timezone
import hashlib,json,unreal

ROOT=Path(unreal.Paths.project_dir());BASE='/Game/LineBoss/Maps/LB_PressShop_NewSegmentedTrains_v748';TARGET='/Game/LineBoss/Maps/LB_PressShop_NewSegmentedTrains_Grounded_v750'
OUT=ROOT/'Saved/Audits/PressShopIntegration/press_shop_grounded_trains_v750.json';PROTECTED=ROOT/'Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap';EXPECTED='5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8'
lib=unreal.EditorAssetLibrary;levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
sha=lambda:hashlib.sha256(PROTECTED.read_bytes()).hexdigest().upper()
if sha()!=EXPECTED:raise RuntimeError('Protected v438 mismatch')
if OUT.exists() or lib.does_asset_exist(TARGET):raise RuntimeError('Refusing overwrite v750')
if not levels.new_level_from_template(TARGET,BASE):raise RuntimeError('Could not derive v750')
changed=[]
for a in actors.get_all_level_actors():
    label=a.get_actor_label();tags={str(t) for t in a.tags};dz=None;kind=None
    if 'LB.PressShop.NewSegmentedTrains.v748' in tags:dz=327.0;kind='transfer'
    elif label.startswith('LB_NEW_TRAIN_') and '_ROLLER_CONVEYOR' in label:dz=100.0;kind='conveyor'
    elif label.startswith('LB_NEW_TRAIN_') and '_S0' in label:dz=411.0;kind='press_cell'
    if dz is not None:
        loc=a.get_actor_location();a.set_actor_location(unreal.Vector(loc.x,loc.y,loc.z+dz),False,False)
        a.tags=list(a.tags)+[unreal.Name('LB.PressShop.Grounded.v750'),unreal.Name(f'LB.GroundCorrection.{kind}.{int(dz)}cm')]
        changed.append({'label':label,'kind':kind,'dz_cm':dz})
if len(changed)!=192:raise RuntimeError(f'Expected 192 corrected train actors, got {len(changed)}')
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.save_current_level():raise RuntimeError('Save v750 failed')
bottoms=[]
for a in actors.get_all_level_actors():
    if 'LB.PressShop.Grounded.v750' in {str(t) for t in a.tags}:
        origin,extent=a.get_actor_bounds(False);bottoms.append({'label':a.get_actor_label(),'bottom_z_cm':origin.z-extent.z,'top_z_cm':origin.z+extent.z})
min_bottom=min(r['bottom_z_cm'] for r in bottoms);max_top=max(r['top_z_cm'] for r in bottoms);fail=[]
if min_bottom < -8.0:fail.append(f'grounded component below tolerance: {min_bottom:.2f} cm')
if sha()!=EXPECTED:fail.append('protected hash changed')
counts={k:sum(1 for r in changed if r['kind']==k) for k in ['press_cell','transfer','conveyor']}
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps({'revision':'v750','generated_utc':datetime.now(timezone.utc).isoformat(),'status':'PASS__ALL_NEW_TRAINS_GROUNDED' if not fail else 'FAIL__V750','map':TARGET,'base':BASE,'corrected_actor_count':len(changed),'counts':counts,'corrections_cm':{'press_cell':411,'transfer':327,'conveyor':100},'minimum_bottom_z_cm':min_bottom,'maximum_top_z_cm':max_top,'bounds':bottoms,'failures':fail,'protected_sha256':sha(),'meshy_credits_used':0},indent=2),encoding='utf-8')
if fail:raise RuntimeError('; '.join(fail))
unreal.log('LINE_BOSS_GROUNDED_NEW_SEGMENTED_TRAINS_V750_PASS')
