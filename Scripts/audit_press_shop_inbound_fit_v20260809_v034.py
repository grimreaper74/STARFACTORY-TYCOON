from pathlib import Path
from datetime import datetime, timezone
import json, unreal

ROOT=Path(unreal.Paths.project_dir())
MAP='/Game/LineBoss/Maps/LB_PressShop_CleanApprovedTrainsFleetPaint_v20260809_v032'
OUT=ROOT/'Saved/Audits/PressShopIntegration/clean_inbound_fit_audit_v20260809_v034.json'
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
assert levels.load_level(MAP)

rows=[]
for a in actors.get_all_level_actors():
    label=a.get_actor_label(); tags={str(x) for x in a.tags}
    if ('LB.Station.PR003' in tags or 'LB.Material.PackagedCoil' in tags or
        label.startswith('LB_CLEAN_Inbound') or label.startswith('LB_CLEAN_PR003') or
        'Lorry' in label or 'CoilPrep' in label or 'Decoiler' in label or 'Threader' in label):
        loc=a.get_actor_location(); origin,extent=a.get_actor_bounds(False)
        rows.append({'label':label,'class':a.get_class().get_name(),'location_cm':[round(loc.x,3),round(loc.y,3),round(loc.z,3)],'bounds_min_cm':[round(origin.x-extent.x,3),round(origin.y-extent.y,3),round(origin.z-extent.z,3)],'bounds_max_cm':[round(origin.x+extent.x,3),round(origin.y+extent.y,3),round(origin.z+extent.z,3)],'size_cm':[round(extent.x*2,3),round(extent.y*2,3),round(extent.z*2,3)],'tags':sorted(tags)})

lorry=[r for r in rows if 'Lorry' in r['label']]
trailer_coils=[r for r in rows if 'TrailerCoil' in r['label']]
trailer_stands=[r for r in rows if 'TrailerStand' in r['label']]
store_coils=[r for r in rows if 'PR003_Coil' in r['label']]
store_stands=[r for r in rows if 'PR003_Stand' in r['label']]

def centres(items,axis): return sorted(round(x['location_cm'][axis],3) for x in items)
def gaps(items,axis):
    vals=centres(items,axis); return [round(vals[i+1]-vals[i],3) for i in range(len(vals)-1)]

checks={
 'exactly_one_lorry':len(lorry)==1,
 'four_trailer_coils':len(trailer_coils)==4,
 'eight_trailer_stands':len(trailer_stands)==8,
 'twelve_storage_coils':len(store_coils)==12,
 'twenty_four_storage_stands':len(store_stands)==24,
 'storage_stands_grounded':all(abs(r['bounds_min_cm'][2])<=0.5 for r in store_stands),
 'storage_coils_above_floor':all(r['bounds_min_cm'][2]>=-0.5 for r in store_coils),
 'trailer_coils_above_floor':all(r['bounds_min_cm'][2]>50 for r in trailer_coils),
}
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps({'generated_utc':datetime.now(timezone.utc).isoformat(),'status':'PASS_EXACT_COUNTS_AND_CONTACT__FIT_REVIEW_REQUIRED' if all(checks.values()) else 'FAIL_INBOUND_FIT','map':MAP,'checks':checks,'counts':{'lorry':len(lorry),'trailer_coils':len(trailer_coils),'trailer_stands':len(trailer_stands),'storage_coils':len(store_coils),'storage_stands':len(store_stands)},'trailer_coil_centres_x_cm':centres(trailer_coils,0),'trailer_coil_gaps_x_cm':gaps(trailer_coils,0),'storage_coil_centres_xy_cm':[[r['location_cm'][0],r['location_cm'][1]] for r in store_coils],'rows':rows,'meshy_credits_used':0},indent=2),encoding='utf-8')
