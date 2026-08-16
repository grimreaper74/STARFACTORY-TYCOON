"""Capture all three fixed-camera Unreal visual gates for complete Train A."""
from pathlib import Path
from datetime import datetime,timezone
import json,time,unreal
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP="/Game/LineBoss/Developer/Validation/PressTrains/LB_PressTrainA_VisualReview_v680";ROOT=Path(unreal.Paths.project_dir());OUT=ROOT/r"Saved\ValidationScreenshots\PressShopIntegration\complete_train_a_v681";AUDIT=ROOT/r"Saved\Audits\PressTrains\complete_train_a_visual_capture_v681.json"
SHOTS=[("LB_CAM_TrainA_OperatorOverview_v680","operator_overview.png"),("LB_CAM_TrainA_ElevatedProcess_v680","elevated_process.png"),("LB_CAM_TrainA_ServiceOverview_v680","service_overview.png")]
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):raise RuntimeError("Could not load v680")
OUT.mkdir(parents=True,exist_ok=True);world=unreal.EditorLevelLibrary.get_editor_world();unreal.SystemLibrary.execute_console_command(world,"viewmode lit");unreal.SystemLibrary.execute_console_command(world,"r.Streaming.FullyLoadUsedTextures 1");unreal.EditorLevelLibrary.editor_set_game_view(True);unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation();unreal.AutomationLibrary.finish_loading_before_screenshot()
index=0;task=None;started=0;handle=None;records=[]
def begin():
 global task,started
 label,filename=SHOTS[index];camera=next((a for a in actors.get_all_level_actors() if a.get_actor_label()==label),None)
 if not camera:raise RuntimeError("Missing camera "+label)
 path=OUT/filename
 if path.exists():path.unlink()
 task=unreal.AutomationLibrary.take_high_res_screenshot(1920,1080,str(path),camera=camera,mask_enabled=False,capture_hdr=False,delay=0,force_game_view=True)
 if not task.is_valid_task():raise RuntimeError("Invalid screenshot task "+label)
 started=time.monotonic()
def tick(_):
 global index,handle
 if not task.is_task_done() and time.monotonic()-started<60:return
 label,filename=SHOTS[index];path=OUT/filename;ok=path.exists() and path.stat().st_size>1024;records.append({"camera":label,"file":str(path),"bytes":path.stat().st_size if path.exists() else 0,"status":"CAPTURE_PASS" if ok else "CAPTURE_FAIL"})
 if not ok:unreal.log_error("LINE_BOSS_TRAIN_A_VISUAL_V681_CAPTURE_FAIL "+label)
 index+=1
 if index<len(SHOTS):begin();return
 if handle:unreal.unregister_slate_post_tick_callback(handle);handle=None
 passed=all(r["status"]=="CAPTURE_PASS" for r in records);AUDIT.parent.mkdir(parents=True,exist_ok=True);AUDIT.write_text(json.dumps({"revision":"v681","generated_utc":datetime.now(timezone.utc).isoformat(),"status":"FRESH_UNREAL_CAPTURES__VISUAL_REVIEW_REQUIRED__NOT_PROMOTED" if passed else "CAPTURE_FAIL__NOT_PROMOTED","map":MAP,"resolution":[1920,1080],"captures":records,"protected_map_modified":False,"promotion_authorized":False},indent=2),encoding="utf-8");(unreal.log if passed else unreal.log_error)("LINE_BOSS_TRAIN_A_VISUAL_V681_"+("PASS" if passed else "FAIL"));unreal.EditorPythonScripting.set_keep_python_script_alive(False);unreal.SystemLibrary.quit_editor()
begin();handle=unreal.register_slate_post_tick_callback(tick)
