"""Non-overwriting fit/light successor of clean inbound v004."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,unreal
ROOT=Path(unreal.Paths.project_dir()).resolve();SRC='/Game/LineBoss/Maps/LB_PressShop_CleanInboundStorage_v20260809_v004';MAP='/Game/LineBoss/Maps/LB_PressShop_CleanInboundStorageFit_v20260809_v005';OUT=ROOT/r'Saved\Audits\PressShopIntegration\clean_inbound_storage_fit_v20260809_v005.json';P=ROOT/r'Content\LineBoss\Maps\LB_PressShop_BuilderAuthorityCandidate_v438.umap';E='5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8'
lib=unreal.EditorAssetLibrary;levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest().upper();before=sha(P)
if before!=E or lib.does_asset_exist(MAP) or OUT.exists():raise RuntimeError('fresh/protected invariant')
if not levels.new_level_from_template(MAP,SRC):raise RuntimeError('copy')
adjusted=[]
for a in actors.get_all_level_actors():
 label=a.get_actor_label();loc=a.get_actor_location()
 if label.startswith('LB_CLEAN_PR003_Stand_'):a.set_actor_location(unreal.Vector(loc.x,loc.y,0),False,False);adjusted.append([label,0])
 elif label.startswith('LB_CLEAN_PR003_Coil_'):a.set_actor_location(unreal.Vector(loc.x,loc.y,112),False,False);adjusted.append([label,112])
 elif label.startswith('LB_CLEAN_IN_TrailerCoil_'):a.set_actor_location(unreal.Vector(loc.x,loc.y,200),False,False);adjusted.append([label,200])
for label,loc,extent,intensity in [('LB_CLEAN_InboundReviewLight_v005',(-9000,-2500,1150),(900,900),65000),('LB_CLEAN_StorageReviewLight_v005',(-2800,0,1250),(3300,2800),90000)]:
 a=actors.spawn_actor_from_class(unreal.RectLight,unreal.Vector(*loc),unreal.Rotator(pitch=-90));a.set_actor_label(label);a.tags=[unreal.Name('LB.CleanRebuild.v20260809.v005'),unreal.Name('LB.Environment.ReviewLighting')];c=a.rect_light_component;c.set_editor_property('intensity',float(intensity));c.set_editor_property('source_width',float(extent[0]));c.set_editor_property('source_height',float(extent[1]));c.set_editor_property('temperature',5200.0);c.set_editor_property('use_temperature',True)
if not levels.save_current_level():raise RuntimeError('save')
after=sha(P)
if after!=before:raise RuntimeError('protected')
mf=ROOT/r'Content\LineBoss\Maps\LB_PressShop_CleanInboundStorageFit_v20260809_v005.umap';OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps({'status':'PASS_FIT_AND_REVIEW_LIGHT_BUILD__VISUAL_REVIEW_REQUIRED','generated_utc':datetime.now(timezone.utc).isoformat(),'source':SRC,'map':MAP,'map_sha256':sha(mf),'adjusted_actor_count':len(adjusted),'fit_rules_cm':{'storage_stand_floor_z':0,'storage_coil_centre_z':112,'trailer_coil_centre_z':200},'review_lights':2,'protected_v438_before':before,'protected_v438_after':after,'meshy_credits_used':0},indent=2),encoding='utf-8');unreal.log('LINE_BOSS_CLEAN_INBOUND_STORAGE_FIT_V005_PASS')
