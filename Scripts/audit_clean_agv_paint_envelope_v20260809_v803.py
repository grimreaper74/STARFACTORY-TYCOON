from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
MAP='/Game/LineBoss/Maps/LB_PressShop_CleanConnectedS07_v20260809_v791'
OUT=ROOT/'Saved/Audits/PressShopIntegration/clean_agv_paint_envelope_v20260809_v803.json'
PROTECTED=ROOT/'Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap'
EXPECTED='5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8'
sha=lambda:hashlib.sha256(PROTECTED.read_bytes()).hexdigest().upper()
if OUT.exists() or sha()!=EXPECTED:raise RuntimeError('fresh/protected invariant')
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):raise RuntimeError('load failed')
records=[]
for actor in actors.get_all_level_actors():
    label=actor.get_actor_label()
    tags=[str(tag) for tag in actor.tags]
    searchable=(label+' '+' '.join(tags)).lower()
    if 'agv' not in searchable:continue
    origin,extent=actor.get_actor_bounds(False)
    records.append({
        'label':label,'class':actor.get_class().get_name(),'tags':tags,
        'location_cm':[actor.get_actor_location().x,actor.get_actor_location().y,actor.get_actor_location().z],
        'bounds_size_cm':[extent.x*2,extent.y*2,extent.z*2],
        'is_paint':'paint' in searchable,'is_charger':'charg' in searchable,'is_handoff':'handoff' in searchable,
    })
records.sort(key=lambda item:item['label'])
paint=[item for item in records if item['is_paint']]
bay=[item for item in records if item['is_charger'] or item['is_handoff']]
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps({
    'generated_utc':datetime.now(timezone.utc).isoformat(),
    'status':'MEASURED_CURRENT_V791_AGV_MARKINGS__COMPARE_TO_V802_ENVELOPE__NO_MAP_CHANGES',
    'map':MAP,'required':{'straight_lane_width_cm':230.0,'bay_length_cm':340.0,'bay_width_cm':230.0,'swept_turn_radius_cm':193.7834},
    'agv_actor_count':len(records),'paint_actor_count':len(paint),'charger_or_handoff_count':len(bay),
    'actors':records,'protected_sha256':sha(),'meshy_credits_used':0,
},indent=2),encoding='utf-8')
unreal.log('LINE_BOSS_CLEAN_AGV_PAINT_ENVELOPE_V803_MEASURED')
