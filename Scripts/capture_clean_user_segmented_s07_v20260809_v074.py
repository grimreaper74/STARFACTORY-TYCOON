from pathlib import Path
from datetime import datetime, timezone
import json,time,unreal
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP="/Game/LineBoss/Maps/LB_PressShop_CleanUserSegmentedS07_v20260809_v073"
ROOT=Path(unreal.Paths.project_dir());OUT=ROOT/"Saved/ValidationScreenshots/PressShopIntegration/clean_user_segmented_s07_v20260809_v074";AUDIT=ROOT/"Saved/Audits/PressShopIntegration/clean_user_segmented_s07_capture_v20260809_v074.json"
VIEWS=[
 ("01_s07_train_ends_a_d_lit.png",unreal.Vector(10800,-4700,3500),unreal.Vector(8550,300,350),66.0),
 ("02_s07_train_a_close_lit.png",unreal.Vector(10300,-4300,1500),unreal.Vector(8600,-2880,250),54.0),
]
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):raise RuntimeError("load failed")
OUT.mkdir(parents=True,exist_ok=True);world=unreal.EditorLevelLibrary.get_editor_world()
for a in actors.get_all_level_actors():
 if "roof" in a.get_actor_label().lower() or "ceiling" in a.get_actor_label().lower():a.set_actor_hidden_in_game(True)
for i,(loc,intensity,radius) in enumerate([(unreal.Vector(9000,-1000,5200),9000,8000),(unreal.Vector(9000,3500,4500),6000,6500)]):
 l=actors.spawn_actor_from_class(unreal.PointLight,loc,unreal.Rotator());l.set_actor_label(f"LB_REVIEW_S07_v074_{i}");l.point_light_component.set_editor_property("intensity",float(intensity));l.point_light_component.set_editor_property("attenuation_radius",float(radius));l.point_light_component.set_editor_property("cast_shadows",False)
cameras=[]
for i,(_,loc,target,fov) in enumerate(VIEWS):
 c=actors.spawn_actor_from_class(unreal.CameraActor,loc,unreal.Rotator());c.set_actor_label(f"LB_CAM_S07_v074_{i}");c.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(loc,target),False);c.camera_component.set_editor_property("field_of_view",fov);cameras.append(c)
unreal.SystemLibrary.execute_console_command(world,"viewmode lit");unreal.SystemLibrary.execute_console_command(world,"r.Streaming.FullyLoadUsedTextures 1");unreal.SystemLibrary.execute_console_command(world,"r.ExposureOffset -0.35");unreal.EditorLevelLibrary.editor_set_game_view(True);unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation();unreal.AutomationLibrary.finish_loading_before_screenshot()
index=0;started=0.0;handle=None;records=[]
def begin():
 global started
 path=OUT/VIEWS[index][0]
 if path.exists():path.unlink()
 task=unreal.AutomationLibrary.take_high_res_screenshot(1920,1080,str(path),camera=cameras[index],mask_enabled=False,capture_hdr=False,delay=2,force_game_view=True)
 if not task.is_valid_task():raise RuntimeError("invalid screenshot")
 started=time.monotonic()
def tick(_):
 global index,handle
 path=OUT/VIEWS[index][0];ok=path.exists() and path.stat().st_size>1024
 if not ok and time.monotonic()-started<90:return
 records.append({"file":str(path),"bytes":path.stat().st_size if path.exists() else 0,"status":"CAPTURE_PASS" if ok else "CAPTURE_FAIL"});index+=1
 if index<len(VIEWS):begin();return
 if handle:unreal.unregister_slate_post_tick_callback(handle);handle=None
 AUDIT.parent.mkdir(parents=True,exist_ok=True);AUDIT.write_text(json.dumps({"generated_utc":datetime.now(timezone.utc).isoformat(),"status":"FRESH_LIT_USER_SEGMENTED_S07__VISUAL_REVIEW_REQUIRED" if all(r["status"]=="CAPTURE_PASS" for r in records) else "CAPTURE_FAIL","map":MAP,"captures":records,"review_lighting":"TRANSIENT_ONLY__MAP_NOT_SAVED","meshy_credits_used":0},indent=2),encoding="utf-8");unreal.EditorPythonScripting.set_keep_python_script_alive(False);unreal.SystemLibrary.quit_editor()
begin();handle=unreal.register_slate_post_tick_callback(tick)
