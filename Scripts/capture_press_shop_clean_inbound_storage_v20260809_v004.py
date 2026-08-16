"""Visual gate for approved lorry, 4 trailer coils, and 12-position store."""
from pathlib import Path
from datetime import datetime,timezone
import json,time,unreal
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP="/Game/LineBoss/Maps/LB_PressShop_CleanInboundStorage_v20260809_v004";ROOT=Path(unreal.Paths.project_dir());OUT=ROOT/r"Saved\ValidationScreenshots\PressShopIntegration\clean_inbound_storage_v20260809_v004";AUDIT=ROOT/r"Saved\Audits\PressShopIntegration\clean_inbound_storage_capture_v20260809_v004.json"
VIEWS=[('inbound_lorry_loaded.png',(-10400,-4200,720),(-9000,-2500,160),52.0),('storage_12_positions.png',(-7600,-4700,1150),(-2800,0,80),60.0),('inbound_and_storage_flow.png',(-10800,-5200,1800),(-2500,0,40),66.0)]
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):raise RuntimeError(MAP)
OUT.mkdir(parents=True,exist_ok=True);world=unreal.EditorLevelLibrary.get_editor_world();unreal.SystemLibrary.execute_console_command(world,'viewmode lit');unreal.SystemLibrary.execute_console_command(world,'r.Streaming.FullyLoadUsedTextures 1');unreal.EditorLevelLibrary.editor_set_game_view(True);unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation();unreal.AutomationLibrary.finish_loading_before_screenshot()
cams=[]
for i,(_,loc,target,fov) in enumerate(VIEWS):
 c=actors.spawn_actor_from_class(unreal.CameraActor,unreal.Vector(*loc),unreal.Rotator());c.set_actor_label(f'LB_TRANSIENT_CleanInboundCamera_{i+1:02d}');c.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(c.get_actor_location(),unreal.Vector(*target)),False);c.camera_component.set_editor_properties({'field_of_view':fov,'aspect_ratio':16/9,'constrain_aspect_ratio':True});cams.append(c)
index=0;task=None;started=0;handle=None;records=[]
def begin():
 global task,started
 path=OUT/VIEWS[index][0]
 if path.exists():path.unlink()
 task=unreal.AutomationLibrary.take_high_res_screenshot(1920,1080,str(path),camera=cams[index],mask_enabled=False,capture_hdr=False,delay=0,force_game_view=True);started=time.monotonic()
def tick(_):
 global index,handle
 if not task.is_task_done() and time.monotonic()-started<60:return
 path=OUT/VIEWS[index][0];ok=path.exists() and path.stat().st_size>1024;records.append({'file':str(path),'bytes':path.stat().st_size if path.exists() else 0,'status':'CAPTURE_PASS' if ok else 'CAPTURE_FAIL'});index+=1
 if index<len(VIEWS):begin();return
 if handle:unreal.unregister_slate_post_tick_callback(handle);handle=None
 passed=all(r['status']=='CAPTURE_PASS' for r in records);AUDIT.parent.mkdir(parents=True,exist_ok=True);AUDIT.write_text(json.dumps({'generated_utc':datetime.now(timezone.utc).isoformat(),'status':'CAPTURE_PASS__VISUAL_REVIEW_REQUIRED' if passed else 'CAPTURE_FAIL','map':MAP,'captures':records,'map_saved_during_capture':False},indent=2),encoding='utf-8');(unreal.log if passed else unreal.log_error)('LINE_BOSS_CLEAN_INBOUND_STORAGE_CAPTURE_V004_'+('PASS' if passed else 'FAIL'));unreal.EditorPythonScripting.set_keep_python_script_alive(False);unreal.SystemLibrary.quit_editor()
begin();handle=unreal.register_slate_post_tick_callback(tick)
