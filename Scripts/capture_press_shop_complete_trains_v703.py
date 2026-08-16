"""Capture three fixed-camera whole-shop views of integrated complete Trains A-D."""
from pathlib import Path
from datetime import datetime,timezone
import json,time,unreal
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP="/Game/LineBoss/Developer/Validation/PressShop/LB_PressShop_CompleteTrainsABCD_Visual_v702"
ROOT=Path(unreal.Paths.project_dir());OUT=ROOT/"Saved/ValidationScreenshots/PressShopIntegration/complete_trains_abcd_v703"
AUDIT=ROOT/"Saved/Audits/PressShopIntegration/press_shop_complete_trains_visual_capture_v703.json"
SHOTS=[("LB_V702_CAM_FourTrainSouthOverview","four_train_south_overview.png"),("LB_V702_CAM_FourTrainHighSouth","four_train_high_south.png"),("LB_V702_CAM_TrainAOperator","train_a_operator_in_shop.png")]
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);api=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):raise RuntimeError(MAP)
OUT.mkdir(parents=True,exist_ok=True);world=unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world,"viewmode lit");unreal.SystemLibrary.execute_console_command(world,"r.Streaming.FullyLoadUsedTextures 1")
unreal.EditorLevelLibrary.editor_set_game_view(True);unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation();unreal.AutomationLibrary.finish_loading_before_screenshot()
index=0;task=None;started=0;handle=None;records=[]
def begin():
 global task,started
 label,name=SHOTS[index];cam=next((a for a in api.get_all_level_actors() if a.get_actor_label()==label),None)
 if not cam:raise RuntimeError("missing "+label)
 path=OUT/name
 if path.exists():path.unlink()
 task=unreal.AutomationLibrary.take_high_res_screenshot(1920,1080,str(path),camera=cam,mask_enabled=False,capture_hdr=False,delay=0,force_game_view=True)
 if not task.is_valid_task():raise RuntimeError("invalid screenshot task")
 started=time.monotonic()
def tick(_):
 global index,handle
 if not task.is_task_done() and time.monotonic()-started<60:return
 label,name=SHOTS[index];path=OUT/name;ok=path.exists() and path.stat().st_size>1024
 records.append({"camera":label,"file":str(path),"bytes":path.stat().st_size if path.exists() else 0,"status":"CAPTURE_PASS" if ok else "CAPTURE_FAIL"})
 index+=1
 if index<len(SHOTS):begin();return
 if handle:unreal.unregister_slate_post_tick_callback(handle);handle=None
 passed=all(r["status"]=="CAPTURE_PASS" for r in records);AUDIT.parent.mkdir(parents=True,exist_ok=True)
 AUDIT.write_text(json.dumps({"revision":"v703","generated_utc":datetime.now(timezone.utc).isoformat(),"status":"FRESH_UNREAL_CAPTURES__VISUAL_REVIEW_REQUIRED" if passed else "CAPTURE_FAIL","map":MAP,"captures":records,"protected_map_modified":False},indent=2),encoding="utf-8")
 (unreal.log if passed else unreal.log_error)("LINE_BOSS_PRESS_SHOP_COMPLETE_TRAINS_V703_"+("PASS" if passed else "FAIL"));unreal.EditorPythonScripting.set_keep_python_script_alive(False);unreal.SystemLibrary.quit_editor()
begin();handle=unreal.register_slate_post_tick_callback(tick)
