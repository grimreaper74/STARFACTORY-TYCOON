from pathlib import Path
from datetime import datetime, timezone
import hashlib,json,unreal
ROOT=Path(unreal.Paths.project_dir());BASE='/Game/LineBoss/Maps/LB_PressShop_CleanMeshyBuild_v720';TARGET='/Game/LineBoss/Maps/LB_PressShop_NewRigidTrains_v743'
OUT=ROOT/'Saved/Audits/PressShopIntegration/press_shop_new_rigid_trains_build_v743.json';PROTECTED=ROOT/'Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap';EXPECTED='5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8'
DEST='/Game/LineBoss/Developer/Validation/PressTrains/NewRigidIntake_v741'
PRESS=DEST+'/Cairnwell_S03_Movable_v632Controls_v735/StaticMeshes/'
TRANSFER=DEST+'/CA_InterPressTransferRigid_v737/StaticMeshes/'
CONVEYOR=DEST+'/Cairnwell_RollerConveyor_Movable_v740/StaticMeshes/'
press_assets=['S03_STATIC_SHELL','S03_RAM_SLIDE','S03_UPPER_DIE','S03_LOWER_DIE_BOLSTER','SM_CA_Factory_Elect_net_MeshyMaster_v632','SM_CA_Factory_Opera_HMI_MeshyMaster_v632']
transfer_assets=['SM_CA_PT_STATIC_RAILS_v737','SM_CA_PT_SERVO_CARRIAGE_v737','SM_CA_PT_CROSSBEAM_Z_v737','SM_CA_PT_GRIPPER_LEFT_v737','SM_CA_PT_GRIPPER_RIGHT_v737']
conveyor_asset='SM_CA_ROLLER_CONVEYO__TEXTURED_STATIC_v740'
lib=unreal.EditorAssetLibrary;levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
def sha():return hashlib.sha256(PROTECTED.read_bytes()).hexdigest().upper()
if sha()!=EXPECTED:raise RuntimeError('Protected v438 mismatch')
if OUT.exists() or lib.does_asset_exist(TARGET):raise RuntimeError('Refusing overwrite v743')
def asset(folder,name):
    p=folder+name+'.'+name;a=unreal.load_asset(p)
    if not isinstance(a,unreal.StaticMesh):raise RuntimeError('Missing '+p)
    return a
press=[asset(PRESS,n) for n in press_assets];transfer=[asset(TRANSFER,n) for n in transfer_assets];conveyor=asset(CONVEYOR,conveyor_asset)
if not levels.new_level_from_template(TARGET,BASE):raise RuntimeError('Could not derive v743')
created=[]
def spawn(mesh,label,loc,scale,tags,movable=False,nav=True):
    a=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(*loc),unreal.Rotator())
    a.set_actor_label(label);a.tags=[unreal.Name(t) for t in tags+['LB.PressShop.NewRigidTrains.v743','LB.Asset.NewVerifiedIntake.v742','LB.Source.NoLegacyMapCopy']]
    c=a.static_mesh_component;c.set_static_mesh(mesh);c.set_world_scale3d(unreal.Vector(scale,scale,scale));c.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS);c.set_editor_property('can_ever_affect_navigation',nav)
    if movable:c.set_mobility(unreal.ComponentMobility.MOVABLE)
    created.append(a);return a
ys={'A':-4300,'B':-2100,'C':100,'D':2300};press_x=[0,2000,4000,6000,8000];transfer_x=[1000,3000,5000,7000]
motion_words={'S03_RAM_SLIDE','S03_UPPER_DIE','S03_LOWER_DIE_BOLSTER','SM_CA_PT_SERVO_CARRIAGE_v737','SM_CA_PT_CROSSBEAM_Z_v737','SM_CA_PT_GRIPPER_LEFT_v737','SM_CA_PT_GRIPPER_RIGHT_v737'}
counts={}
for train,y in ys.items():
    counts[train]={'press_cells':0,'transfer_modules':0,'conveyors':0,'actors':0}
    for si,x in enumerate(press_x,2):
        for name,mesh in zip(press_assets,press):
            tags=[f'LB.PressTrain.Installed.TRAIN_{train}',f'LB.PressTrain.Station.S{si:02d}',f'LB.Component.{name}']
            spawn(mesh,f'LB_NEW_TRAIN_{train}_S{si:02d}_{name}',(x,y,0),6.57,tags,name in motion_words,not name in motion_words);counts[train]['actors']+=1
        counts[train]['press_cells']+=1
    for ti,x in enumerate(transfer_x,2):
        for name,mesh in zip(transfer_assets,transfer):
            tags=[f'LB.PressTrain.Installed.TRAIN_{train}',f'LB.Transfer.S{ti:02d}_S{ti+1:02d}',f'LB.Component.{name}']
            spawn(mesh,f'LB_NEW_TRAIN_{train}_TR_{ti:02d}_{name}',(x,y,0),5.0,tags,name in motion_words,not name in motion_words);counts[train]['actors']+=1
        counts[train]['transfer_modules']+=1
    for end,x in [('INFEED',-1200),('OUTFEED',9400)]:
        spawn(conveyor,f'LB_NEW_TRAIN_{train}_{end}_ROLLER_CONVEYOR',(x,y,0),1.55,[f'LB.PressTrain.Installed.TRAIN_{train}',f'LB.Conveyor.{end}','LB.Component.PoweredRollerConveyor'],False,True);counts[train]['actors']+=1;counts[train]['conveyors']+=1
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.save_current_level():raise RuntimeError('Save v743 failed')
fail=[]
if len(created)!=208:fail.append(f'created {len(created)} expected 208')
for t,c in counts.items():
    if c!={'press_cells':5,'transfer_modules':4,'conveyors':2,'actors':52}:fail.append(f'{t}:{c}')
if sha()!=EXPECTED:fail.append('protected hash changed')
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps({'revision':'v743','generated_utc':datetime.now(timezone.utc).isoformat(),'status':'PASS__CLEAN_NEW_RIGID_TRAINS_A_D' if not fail else 'FAIL__V743','map':TARGET,'base':BASE,'created_actor_count':len(created),'counts':counts,'train_datums_cm':{k:[1600,v,0] for k,v in ys.items()},'press_centres_x_cm':press_x,'transfer_centres_x_cm':transfer_x,'conveyor_centres_x_cm':[-1200,9400],'press_uniform_scale':6.57,'transfer_uniform_scale':5.0,'conveyor_uniform_scale':1.55,'failures':fail,'protected_sha256':sha(),'meshy_credits_used':0},indent=2),encoding='utf-8')
if fail:raise RuntimeError(';'.join(fail))
unreal.log('LINE_BOSS_CLEAN_NEW_RIGID_TRAINS_V743_PASS')
