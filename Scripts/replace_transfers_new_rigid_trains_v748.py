from pathlib import Path
from datetime import datetime, timezone
import hashlib,json,unreal

ROOT=Path(unreal.Paths.project_dir());BASE='/Game/LineBoss/Maps/LB_PressShop_NewRigidTrains_v743';TARGET='/Game/LineBoss/Maps/LB_PressShop_NewSegmentedTrains_v748'
OUT=ROOT/'Saved/Audits/PressShopIntegration/press_shop_segmented_transfer_replacement_v748.json';PROTECTED=ROOT/'Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap';EXPECTED='5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8'
DEST='/Game/LineBoss/Developer/Validation/PressTrains/SegmentedTransferRuntime_v747'
lib=unreal.EditorAssetLibrary;levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
sha=lambda:hashlib.sha256(PROTECTED.read_bytes()).hexdigest().upper()
if sha()!=EXPECTED:raise RuntimeError('Protected v438 mismatch')
if OUT.exists() or lib.does_asset_exist(TARGET):raise RuntimeError('Refusing overwrite v748')
mesh_paths=[]
for p in lib.list_assets(DEST,recursive=True,include_folder=False):
    a=unreal.load_asset(p)
    if isinstance(a,unreal.StaticMesh):mesh_paths.append(p)
fragments=['TIC_FRAME','CROSSBEAM','ATOR_PACK','CUP_ARRAY']
meshes=[]
for frag in fragments:
    hits=[p for p in mesh_paths if frag.lower() in p.lower()]
    if len(hits)!=1:raise RuntimeError(f'{frag} resolved to {hits}')
    meshes.append(unreal.load_asset(hits[0]))
if not levels.new_level_from_template(TARGET,BASE):raise RuntimeError('Could not derive v748')
old=[]
for a in actors.get_all_level_actors():
    tags={str(t) for t in a.tags}
    if any(t.startswith('LB.Transfer.') for t in tags) and 'LB.PressShop.NewRigidTrains.v743' in tags:old.append(a)
if len(old)!=80:raise RuntimeError(f'Expected 80 old transfer actors, found {len(old)}')
actors.destroy_actors(old)
ys={'A':-4300,'B':-2100,'C':100,'D':2300};xs=[1000,3000,5000,7000];created=[]
for train,y in ys.items():
    for gap,x in enumerate(xs,2):
        for frag,mesh in zip(fragments,meshes):
            a=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(x,y,0),unreal.Rotator())
            a.set_actor_label(f'LB_NEW_TRAIN_{train}_TR_{gap:02d}_{frag}_v748')
            a.tags=[unreal.Name(t) for t in [f'LB.PressTrain.Installed.TRAIN_{train}',f'LB.Transfer.S{gap:02d}_S{gap+1:02d}',f'LB.Component.SegmentedTransfer.{frag}','LB.PressShop.NewSegmentedTrains.v748','LB.Asset.SegmentedRuntime.v747b','LB.Source.NoLegacyMapCopy']]
            c=a.static_mesh_component;c.set_static_mesh(mesh);c.set_world_scale3d(unreal.Vector(6.0,6.0,6.0));c.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
            movable=frag!='TIC_FRAME';c.set_mobility(unreal.ComponentMobility.MOVABLE if movable else unreal.ComponentMobility.STATIC);c.set_editor_property('can_ever_affect_navigation',not movable)
            created.append(a)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.save_current_level():raise RuntimeError('Save v748 failed')
all_actors=actors.get_all_level_actors();fail=[]
if len(created)!=64:fail.append(f'created {len(created)} expected 64')
remaining_old=[a.get_actor_label() for a in all_actors if any(str(t).startswith('LB.Transfer.') for t in a.tags) and 'LB.PressShop.NewRigidTrains.v743' in {str(t) for t in a.tags}]
if remaining_old:fail.append(f'old transfer actors remain: {len(remaining_old)}')
if sha()!=EXPECTED:fail.append('protected hash changed')
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps({'revision':'v748','generated_utc':datetime.now(timezone.utc).isoformat(),'status':'PASS__SEGMENTED_TRANSFERS_REPLACE_PROCEDURAL' if not fail else 'FAIL__V748','map':TARGET,'base':BASE,'deleted_old_transfer_actors':len(old),'created_segmented_transfer_actors':len(created),'total_level_actors':len(all_actors),'train_y_cm':ys,'transfer_x_cm':xs,'uniform_scale':6.0,'logical_components':fragments,'failures':fail,'protected_sha256':sha(),'meshy_credits_used':0},indent=2),encoding='utf-8')
if fail:raise RuntimeError('; '.join(fail))
unreal.log('LINE_BOSS_SEGMENTED_TRANSFER_REPLACEMENT_V748_PASS')
