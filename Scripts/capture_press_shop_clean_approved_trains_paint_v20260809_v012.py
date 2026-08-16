"""Capture evidence for clean approved trains and complete floor-paint pass."""
from pathlib import Path
import json, unreal
MAP='/Game/LineBoss/Maps/LB_PressShop_CleanApprovedTrainsFleetLit_v20260809_v018'
ROOT=Path(unreal.Paths.project_dir());OUT=ROOT/r'Saved\ValidationScreenshots\PressShopIntegration\clean_approved_trains_fleet_lit_v20260809_v018';AUDIT=ROOT/r'Saved\Audits\PressShopIntegration\clean_approved_trains_fleet_lit_capture_v20260809_v018.json'
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):raise RuntimeError('load')
OUT.mkdir(parents=True,exist_ok=True);world=unreal.EditorLevelLibrary.get_editor_world();unreal.SystemLibrary.execute_console_command(world,'viewmode lit');unreal.SystemLibrary.execute_console_command(world,'r.Streaming.FullyLoadUsedTextures 1');unreal.SystemLibrary.execute_console_command(world,'r.ExposureOffset 0.8');unreal.EditorLevelLibrary.editor_set_game_view(True);unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation();unreal.AutomationLibrary.finish_loading_before_screenshot()
views=[('train_a_broadside_face_lit',(5000,-5200,720),(5000,-3300,320),90)]
cams=[];files=[]
for i,(name,loc,target,fov) in enumerate(views):
 c=actors.spawn_actor_from_class(unreal.CameraActor,unreal.Vector(*loc),unreal.Rotator());c.set_actor_label(f'LB_TRANSIENT_v012_{i:02d}');c.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(c.get_actor_location(),unreal.Vector(*target)),False);c.camera_component.set_editor_properties({'field_of_view':fov,'aspect_ratio':16/9,'constrain_aspect_ratio':True});cams.append(c);p=OUT/f'{name}.png';files.append(str(p));unreal.AutomationLibrary.take_high_res_screenshot(1920,1080,str(p),camera=c,mask_enabled=False,capture_hdr=False,delay=0.25,force_game_view=True)
# The screenshot request is asynchronous. Keep the transient camera alive until editor shutdown.
AUDIT.parent.mkdir(parents=True,exist_ok=True);AUDIT.write_text(json.dumps({'status':'CAPTURE_REQUESTED__FILES_REQUIRE_EXISTENCE_CHECK','map':MAP,'screenshots':files},indent=2),encoding='utf-8');unreal.log('LINE_BOSS_CLEAN_APPROVED_TRAINS_PAINT_CAPTURE_V013_REQUESTED')
