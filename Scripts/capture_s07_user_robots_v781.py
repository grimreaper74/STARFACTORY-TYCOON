from pathlib import Path
from datetime import datetime,timezone
import json,time,unreal
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP='/Game/LineBoss/Maps/LB_PressShop_Trains_Inbound_UserS07_v780';ROOT=Path(unreal.Paths.project_dir());OUT=ROOT/'Saved/ValidationScreenshots/PressShopIntegration/s07_user_robots_v781';AUDIT=ROOT/'Saved/Audits/PressShopIntegration/s07_user_robot_capture_v781.json'
VIEWS=[
 ('train_a_user_robot_close.png',unreal.Vector(10300,-6000,1050),unreal.Vector(8600,-3880,210),54.),
 ('four_user_robots_row.png',unreal.Vector(10600,-650,1900),unreal.Vector(8600,-600,220),60.),
 ('user_robots_with_press_trains.png',unreal.Vector(11300,-6800,3300),unreal.Vector(6500,-800,350),70.),
]
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):raise RuntimeError('Could not load v780')
OUT.mkdir(parents=True,exist_ok=True);world=unreal.EditorLevelLibrary.get_editor_world();unreal.SystemLibrary.execute_console_command(world,'viewmode lit');unreal.SystemLibrary.execute_console_command(world,'r.Streaming.FullyLoadUsedTextures 1');unreal.SystemLibrary.execute_console_command(world,'r.ExposureOffset 2.0');unreal.EditorLevelLibrary.editor_set_game_view(True);unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation();unreal.AutomationLibrary.finish_loading_before_screenshot();cams=[]
for fn,loc,target,fov in VIEWS:
 c=actors.spawn_actor_from_class(unreal.CameraActor,loc,unreal.Rotator());c.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(loc,target),False);c.camera_component.set_editor_property('field_of_view',fov);cams.append(c)
i=0;task=None;started=0.;handle=None;records=[]
def begin():
 global task,started
 p=OUT/VIEWS[i][0]
 if p.exists():p.unlink()
 task=unreal.AutomationLibrary.take_high_res_screenshot(1920,1080,str(p),camera=cams[i],mask_enabled=False,capture_hdr=False,delay=0,force_game_view=True);started=time.monotonic()
def tick(_):
 global i,handle
 p=OUT/VIEWS[i][0]
 if not(p.exists() and p.stat().st_size>1024) and time.monotonic()-started<90:return
 ok=p.exists() and p.stat().st_size>1024;records.append({'file':str(p),'bytes':p.stat().st_size if p.exists() else 0,'status':'CAPTURE_PASS' if ok else 'CAPTURE_FAIL'});i+=1
 if i<len(VIEWS):begin();return
 if handle:unreal.unregister_slate_post_tick_callback(handle);handle=None
 AUDIT.parent.mkdir(parents=True,exist_ok=True);AUDIT.write_text(json.dumps({'revision':'v781','generated_utc':datetime.now(timezone.utc).isoformat(),'status':'FRESH_USER_S07_VISUAL_RECEIPTS','map':MAP,'captures':records,'map_saved':False,'meshy_credits_used_by_codex':0},indent=2),encoding='utf-8');unreal.EditorPythonScripting.set_keep_python_script_alive(False);unreal.SystemLibrary.quit_editor()
begin();handle=unreal.register_slate_post_tick_callback(tick)
