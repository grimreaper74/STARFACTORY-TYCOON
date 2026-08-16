"""Capture the fresh empty 220 x 120 m shell without saving camera actors."""
from pathlib import Path
from datetime import datetime, timezone
import json, time, unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP="/Game/LineBoss/Maps/LB_PressShop_CleanShell_v20260809_v001"
ROOT=Path(unreal.Paths.project_dir())
OUT=ROOT/"Saved/ValidationScreenshots/PressShopIntegration/clean_shell_v20260809_v001"
AUDIT=ROOT/"Saved/Audits/PressShopIntegration/clean_shell_capture_v20260809_v001.json"
VIEWS=[
 ("whole_shell_south_east.png",(9200,-4100,1450),(0,0,100),65.0),
 ("fixed_walkway_and_fire_paint.png",(7600,-3000,520),(8500,-5100,5),52.0),
 ("inbound_review_zone_empty.png",(-9800,-3600,820),(-7500,0,30),58.0),
]
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP): raise RuntimeError(MAP)
OUT.mkdir(parents=True,exist_ok=True)
world=unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world,"viewmode lit")
unreal.SystemLibrary.execute_console_command(world,"r.Streaming.FullyLoadUsedTextures 1")
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()
cams=[]
for i,(_,loc,target,fov) in enumerate(VIEWS):
 c=actors.spawn_actor_from_class(unreal.CameraActor,unreal.Vector(*loc),unreal.Rotator())
 c.set_actor_label(f"LB_TRANSIENT_CleanShellCamera_{i+1:02d}")
 c.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(c.get_actor_location(),unreal.Vector(*target)),False)
 c.camera_component.set_editor_properties({"field_of_view":fov,"aspect_ratio":16/9,"constrain_aspect_ratio":True})
 cams.append(c)
index=0;task=None;started=0;handle=None;records=[]
def begin():
 global task,started
 name,_,_,_=VIEWS[index];path=OUT/name
 if path.exists():path.unlink()
 task=unreal.AutomationLibrary.take_high_res_screenshot(1920,1080,str(path),camera=cams[index],mask_enabled=False,capture_hdr=False,delay=0,force_game_view=True)
 if not task.is_valid_task():raise RuntimeError("invalid screenshot task")
 started=time.monotonic()
def tick(_):
 global index,handle
 if not task.is_task_done() and time.monotonic()-started<60:return
 name,_,_,_=VIEWS[index];path=OUT/name;ok=path.exists() and path.stat().st_size>1024
 records.append({"file":str(path),"bytes":path.stat().st_size if path.exists() else 0,"status":"CAPTURE_PASS" if ok else "CAPTURE_FAIL"})
 index+=1
 if index<len(VIEWS):begin();return
 if handle:unreal.unregister_slate_post_tick_callback(handle);handle=None
 passed=all(r["status"]=="CAPTURE_PASS" for r in records)
 AUDIT.parent.mkdir(parents=True,exist_ok=True)
 AUDIT.write_text(json.dumps({"generated_utc":datetime.now(timezone.utc).isoformat(),"status":"FRESH_UNREAL_CAPTURES__VISUAL_REVIEW_REQUIRED" if passed else "CAPTURE_FAIL","map":MAP,"captures":records,"map_saved_during_capture":False},indent=2),encoding="utf-8")
 (unreal.log if passed else unreal.log_error)("LINE_BOSS_CLEAN_SHELL_CAPTURE_V001_"+("PASS" if passed else "FAIL"))
 unreal.EditorPythonScripting.set_keep_python_script_alive(False);unreal.SystemLibrary.quit_editor()
begin();handle=unreal.register_slate_post_tick_callback(tick)
