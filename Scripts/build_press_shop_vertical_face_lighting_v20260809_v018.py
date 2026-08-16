"""Add restrained shadow-free service fill for vertical press faces."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,unreal
ROOT=Path(unreal.Paths.project_dir()).resolve();SOURCE='/Game/LineBoss/Maps/LB_PressShop_CleanApprovedTrainsFleetLit_v20260809_v017';MAP='/Game/LineBoss/Maps/LB_PressShop_CleanApprovedTrainsFleetLit_v20260809_v018';OUT=ROOT/r'Saved\Audits\PressShopIntegration\clean_press_face_lighting_v20260809_v018.json';P=ROOT/r'Content\LineBoss\Maps\LB_PressShop_BuilderAuthorityCandidate_v438.umap';E='5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8'
lib=unreal.EditorAssetLibrary;levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest().upper();before=sha(P)
if before!=E or lib.does_asset_exist(MAP) or OUT.exists():raise RuntimeError('fresh/protected invariant')
if not levels.new_level_from_template(MAP,SOURCE):raise RuntimeError('map child')
created=[]
for y in (-3300,-1100,1100,3300):
 for x in (2600,5000,7400):
  l=actors.spawn_actor_from_class(unreal.PointLight,unreal.Vector(x,y-500,420),unreal.Rotator());l.set_actor_label(f'LB_CLEAN_PressFaceFill_{x}_{y}');c=l.get_component_by_class(unreal.PointLightComponent);c.set_editor_properties({'intensity':4200.0,'attenuation_radius':1050.0,'light_color':unreal.Color(210,225,255,255),'cast_shadows':False});l.tags=[unreal.Name('LB.CleanRebuild.v20260809.v018'),unreal.Name('LB.Lighting.PressFaceFill')];created.append(l)
if not levels.save_current_level():raise RuntimeError('save')
after=sha(P)
if after!=before:raise RuntimeError('protected changed')
mf=ROOT/r'Content\LineBoss\Maps\LB_PressShop_CleanApprovedTrainsFleetLit_v20260809_v018.umap';OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps({'status':'PASS_BUILD__VERTICAL_PRESS_FACE_SERVICE_FILL__VISUAL_REVIEW_REQUIRED__NOT_PROMOTED','generated_utc':datetime.now(timezone.utc).isoformat(),'source':SOURCE,'map':MAP,'map_sha256':sha(mf),'point_fill_count':len(created),'settings':{'intensity':4200,'attenuation_radius_cm':1050,'cast_shadows':False},'meshy_credits_used':0,'protected_v438_before':before,'protected_v438_after':after},indent=2),encoding='utf-8');unreal.log('LINE_BOSS_PRESS_FACE_LIGHTING_V018_PASS')
