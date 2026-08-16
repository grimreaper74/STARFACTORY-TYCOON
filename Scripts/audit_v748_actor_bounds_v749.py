from pathlib import Path
import json, unreal

MAP='/Game/LineBoss/Maps/LB_PressShop_NewSegmentedTrains_v748'
OUT=Path(unreal.Paths.project_dir())/'Saved/Audits/PressShopIntegration/press_shop_v748_actor_bounds_v749.json'
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):raise RuntimeError('Could not load v748')
rows=[]
for a in actors.get_all_level_actors():
    label=a.get_actor_label()
    if label.startswith('LB_NEW_TRAIN_A_'):
        origin,extent=a.get_actor_bounds(False)
        rows.append({'label':label,'location_cm':[a.get_actor_location().x,a.get_actor_location().y,a.get_actor_location().z],'bounds_origin_cm':[origin.x,origin.y,origin.z],'bounds_size_cm':[extent.x*2,extent.y*2,extent.z*2]})
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps({'map':MAP,'train_a_actor_count':len(rows),'actors':rows},indent=2),encoding='utf-8')
unreal.log('LINE_BOSS_V748_BOUNDS_V749_WRITTEN')
