"""Capture one upright, neutrally lit Train A v310 view."""
import os,time
from pathlib import Path
import unreal
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP="/Game/LineBoss/Maps/LB_PressTrainA_LitAxisReviewCandidate_v310";CAP={"operator":("LB_V309_CAM_Operator","v310_train_a_operator.png"),"rear":("LB_V309_CAM_Rear","v310_train_a_rear.png"),"elevated":("LB_V309_CAM_Elevated","v310_train_a_elevated.png")};cid=os.environ.get("LB_V310_CAPTURE","operator").lower();label,name=CAP[cid];out=Path(unreal.Paths.project_saved_dir())/"ValidationScreenshots/PressShopIntegration/v310_train_a_lit_axis_review"/name
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);api=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):raise RuntimeError(MAP)
cam=next((a for a in api.get_all_level_actors() if a.get_actor_label()==label),None)
if cam is None:raise RuntimeError(label)
out.parent.mkdir(parents=True,exist_ok=True)
if out.exists():out.unlink()
world=unreal.EditorLevelLibrary.get_editor_world();unreal.SystemLibrary.execute_console_command(world,"viewmode lit");unreal.SystemLibrary.execute_console_command(world,"r.HighResScreenshotDelay 24");unreal.EditorLevelLibrary.editor_set_game_view(True);unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation();unreal.AutomationLibrary.finish_loading_before_screenshot();task=unreal.AutomationLibrary.take_high_res_screenshot(1920,1080,str(out),camera=cam,mask_enabled=False,capture_hdr=False,comparison_tolerance=unreal.ComparisonTolerance.LOW,comparison_notes=f"Train A v310 {cid}",delay=0,force_game_view=True)
if not task.is_valid_task():raise RuntimeError("invalid screenshot")
started=time.monotonic();handle=None
def done(_):
 global handle
 elapsed=time.monotonic()-started
 if elapsed>=3 and out.exists() and out.stat().st_size>=1024:unreal.log(f"LB_V310_CAPTURE_PASS id={cid} path={out}")
 elif elapsed<70:return
 else:unreal.log_error(f"LB_V310_CAPTURE_FAIL id={cid}")
 if handle is not None:unreal.unregister_slate_post_tick_callback(handle);handle=None
 unreal.EditorPythonScripting.set_keep_python_script_alive(False)
handle=unreal.register_slate_post_tick_callback(done)
