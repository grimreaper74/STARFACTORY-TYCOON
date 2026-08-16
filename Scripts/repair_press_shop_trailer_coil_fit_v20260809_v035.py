from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
SOURCE='/Game/LineBoss/Maps/LB_PressShop_CleanApprovedTrainsFleetPaint_v20260809_v032'
TARGET='/Game/LineBoss/Maps/LB_PressShop_CleanInboundFlowFit_v20260809_v035'
OUT=ROOT/'Saved/Audits/PressShopIntegration/clean_inbound_trailer_fit_v20260809_v035.json'
PROTECTED=ROOT/'Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap'
EXPECTED='5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
before=sha(PROTECTED);assert before==EXPECTED
lib=unreal.EditorAssetLibrary;levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
assert not lib.does_asset_exist(TARGET)
assert levels.new_level_from_template(TARGET,SOURCE)

all_actors={a.get_actor_label():a for a in actors.get_all_level_actors()}
lorry=all_actors.get('LB_CLEAN_IN_Lorry_v006');assert lorry
new_centres=(-3100.0,-2700.0,-2300.0,-1900.0)
records=[]
for i,cy in enumerate(new_centres,1):
    coil=all_actors.get(f'LB_CLEAN_IN_TrailerCoil_{i:02d}')
    stand_a=all_actors.get(f'LB_CLEAN_IN_TrailerStand_{i:02d}_A')
    stand_b=all_actors.get(f'LB_CLEAN_IN_TrailerStand_{i:02d}_B')
    assert coil and stand_a and stand_b
    coil.set_actor_location(unreal.Vector(-9000.0,cy,220.0),False,False)
    stand_a.set_actor_location(unreal.Vector(-9000.0,cy-60.0,111.0),False,False)
    stand_b.set_actor_location(unreal.Vector(-9000.0,cy+60.0,111.0),False,False)
    co,ce=coil.get_actor_bounds(False);ao,ae=stand_a.get_actor_bounds(False);bo,be=stand_b.get_actor_bounds(False)
    records.append({'index':i,'coil_centre_cm':[co.x,co.y,co.z],'coil_bottom_z_cm':co.z-ce.z,'stand_top_z_cm':max(ao.z+ae.z,bo.z+be.z),'support_overlap_cm':max(ao.z+ae.z,bo.z+be.z)-(co.z-ce.z),'chock_outer_width_y_cm':(bo.y+be.y)-(ao.y-ae.y)})

lo,le=lorry.get_actor_bounds(False);lorry_min_y=lo.y-le.y;lorry_max_y=lo.y+le.y
all_inside=all(lorry_min_y <= r['coil_centre_cm'][1]-95 and r['coil_centre_cm'][1]+95 <= lorry_max_y for r in records)
gaps=[new_centres[i+1]-new_centres[i] for i in range(3)]
assert all_inside and gaps==[400.0,400.0,400.0]
assert levels.save_current_level()
after=sha(PROTECTED);assert after==before
map_file=ROOT/'Content/LineBoss/Maps/LB_PressShop_CleanInboundFlowFit_v20260809_v035.umap'
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps({'status':'PASS_TRAILER_COILS_RAISED_SPACED_AND_CHOCKS_WIDENED__VISUAL_REVIEW_REQUIRED','generated_utc':datetime.now(timezone.utc).isoformat(),'source':SOURCE,'map':TARGET,'map_sha256':sha(map_file),'lorry_y_envelope_cm':[lorry_min_y,lorry_max_y],'coil_centres_y_cm':list(new_centres),'coil_centre_gaps_cm':gaps,'coil_centre_z_cm':220.0,'chock_offset_from_coil_centre_y_cm':60.0,'all_coils_inside_trailer':all_inside,'records':records,'meshy_credits_used':0,'protected_v438_before':before,'protected_v438_after':after},indent=2),encoding='utf-8')
unreal.log('LINE_BOSS_CLEAN_INBOUND_TRAILER_FIT_V035_PASS')
