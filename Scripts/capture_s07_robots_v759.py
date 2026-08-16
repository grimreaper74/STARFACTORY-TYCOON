from pathlib import Path
from datetime import datetime,timezone
import json,time,unreal
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP='/Game/LineBoss/Maps/LB_PressShop_GroundedTrains_S07Robots_v758';ROOT=Path(unreal.Paths.project_dir());OUT=ROOT/'Saved/ValidationScreenshots/PressShopIntegration/s07_robots_v759';AUDIT=ROOT/'Saved/Audits/PressShopIntegration/s07_robots_capture_v759.json'
VIEWS=[('train_a_s07_close.png',unreal.Vector(9400,-5200,950),unreal.Vector(8500,-3900,160),58.0),('s07_row_elevated.png',unreal.Vector(10300,-500,2600),unreal.Vector(8600,-500,150),62.0)]
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):raise RuntimeError('Could not load v758')
OUT.mkdir(parents=True,exist_ok=True);world=unreal.EditorLevelLibrary.get_editor_world();unreal.SystemLibrary.execute_console_command(world,'viewmode lit');unreal.SystemLibrary.execute_console_command(world,'r.Streaming.FullyLoadUsedTextures 1');unreal.SystemLibrary.execute_console_command(world,'r.ExposureOffset 2.0');unreal.EditorLevelLibrary.editor_set_game_view(True);unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation();unreal.AutomationLibrary.finish_loading_before_screenshot()
cams=[]
for i,(fn,loc,target,fov) in enumerate(VIEWS):
 c=actors.spawn_actor_from_class(unreal.CameraActor,loc,unreal.Rotator());c.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(loc,target),False);c.camera_component.set_editor_property('field_of_view',fov);cams.append(c)
index=0;task=None;started=0.;handle=None;records=[]
def begin():
 global task,started
 p=OUT/VIEWS[index][0]
 if p.exists():p.unlink()
 task=unreal.AutomationLibrary.take_high_res_screenshot(1920,1080,str(p),camera=cams[index],mask_enabled=False,capture_hdr=False,delay=0,force_game_view=True);started=time.monotonic()
def tick(_):
 global index,handle
 p=OUT/VIEWS[index][0]
 if not(p.exists() and p.stat().st_size>1024) and time.monotonic()-started<90:return
 ok=p.exists() and p.stat().st_size>1024;records.append({'file':str(p),'bytes':p.stat().st_size if p.exists() else 0,'status':'CAPTURE_PASS' if ok else 'CAPTURE_FAIL'});index+=1
 if index<len(VIEWS):begin();return
 if handle:unreal.unregister_slate_post_tick_callback(handle);handle=None
 passed=all(r['status']=='CAPTURE_PASS' for r in records);AUDIT.parent.mkdir(parents=True,exist_ok=True);AUDIT.write_text(json.dumps({'revision':'v759','generated_utc':datetime.now(timezone.utc).isoformat(),'status':'FRESH_S07_ROBOT_VISUAL_RECEIPTS' if passed else 'CAPTURE_FAIL','map':MAP,'captures':records,'map_saved':False,'meshy_credits_used':0},indent=2),encoding='utf-8');unreal.EditorPythonScripting.set_keep_python_script_alive(False);unreal.SystemLibrary.quit_editor()
begin();handle=unreal.register_slate_post_tick_callback(tick)
