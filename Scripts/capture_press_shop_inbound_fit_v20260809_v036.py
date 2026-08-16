from pathlib import Path
from datetime import datetime, timezone
import json,time,unreal
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP='/Game/LineBoss/Maps/LB_PressShop_CleanInboundFlowFit_v20260809_v035'
ROOT=Path(unreal.Paths.project_dir());OUT=ROOT/'Saved/ValidationScreenshots/PressShopIntegration/clean_inbound_fit_v20260809_v037';AUDIT=ROOT/'Saved/Audits/PressShopIntegration/clean_inbound_fit_capture_v20260809_v037.json'
VIEWS=[
 ('lorry_loaded_side.png',unreal.Vector(-6800,-2500,1050),unreal.Vector(-9000,-2500,180),55.0),
 ('lorry_loaded_rear_oblique.png',unreal.Vector(-7600,-4300,1350),unreal.Vector(-9000,-2500,200),58.0),
 ('storage_overview.png',unreal.Vector(-8000,-5000,3100),unreal.Vector(-2600,0,150),64.0),
]
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
assert levels.load_level(MAP);OUT.mkdir(parents=True,exist_ok=True)
world=unreal.EditorLevelLibrary.get_editor_world()
for a in actors.get_all_level_actors():
 label=a.get_actor_label().lower()
 if 'roof' in label or 'ceiling' in label:a.set_actor_hidden_in_game(True)
unreal.SystemLibrary.execute_console_command(world,'viewmode lit');unreal.SystemLibrary.execute_console_command(world,'r.Streaming.FullyLoadUsedTextures 1');unreal.SystemLibrary.execute_console_command(world,'r.ExposureOffset 1.2');unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation();unreal.AutomationLibrary.finish_loading_before_screenshot()
c=[]
for i,(_,loc,target,fov) in enumerate(VIEWS):
 cam=actors.spawn_actor_from_class(unreal.CameraActor,loc,unreal.Rotator());cam.set_actor_label(f'LB_CAM_InboundFit_v037_{i}');cam.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(loc,target),False);cam.camera_component.set_editor_property('field_of_view',fov);c.append(cam)
index=0;task=None;started=0;handle=None;records=[]
def begin():
 global task,started
 fn,_,_,_=VIEWS[index];p=OUT/fn
 if p.exists():p.unlink()
 task=unreal.AutomationLibrary.take_high_res_screenshot(1920,1080,str(p),camera=c[index],mask_enabled=False,capture_hdr=False,delay=0,force_game_view=True);started=time.monotonic()
def tick(_):
 global index,handle
 fn,_,_,_=VIEWS[index];p=OUT/fn
 if not(p.exists() and p.stat().st_size>1024) and time.monotonic()-started<90:return
 ok=p.exists() and p.stat().st_size>1024;records.append({'file':str(p),'bytes':p.stat().st_size if p.exists() else 0,'status':'PASS' if ok else 'FAIL'});index+=1
 if index<len(VIEWS):begin();return
 if handle:unreal.unregister_slate_post_tick_callback(handle);handle=None
 AUDIT.parent.mkdir(parents=True,exist_ok=True);AUDIT.write_text(json.dumps({'generated_utc':datetime.now(timezone.utc).isoformat(),'status':'FRESH_CAPTURES__VISUAL_REVIEW_REQUIRED','map':MAP,'captures':records,'meshy_credits_used':0},indent=2),encoding='utf-8');unreal.EditorPythonScripting.set_keep_python_script_alive(False);unreal.SystemLibrary.quit_editor()
begin();handle=unreal.register_slate_post_tick_callback(tick)
