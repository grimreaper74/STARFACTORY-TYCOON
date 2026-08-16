"""Capture the opposite-axis Train A from its other broad face."""
import time
from pathlib import Path
import unreal
unreal.EditorPythonScripting.set_keep_python_script_alive(True);MAP="/Game/LineBoss/Maps/LB_PressTrainA_OppositeAxisReviewCandidate_v321";out=Path(unreal.Paths.project_saved_dir())/"ValidationScreenshots/PressShopIntegration/v322_train_a_opposite_axis_other_face/v322_train_a_other_face.png";levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);api=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):raise RuntimeError(MAP)
cam=next((a for a in api.get_all_level_actors() if a.get_actor_label()=="LB_V307_CAM_Rear"),None)
if cam is None:raise RuntimeError("camera missing")
out.parent.mkdir(parents=True,exist_ok=True)
if out.exists():raise RuntimeError(f"refusing to overwrite {out}")
world=unreal.EditorLevelLibrary.get_editor_world();unreal.AutomationLibrary.set_editor_viewport_view_mode(unreal.ViewModeIndex.VMI_LIT);unreal.AutomationLibrary.set_editor_active_viewport_view_mode(unreal.ViewModeIndex.VMI_LIT);unreal.SystemLibrary.execute_console_command(world,"viewmode lit");unreal.SystemLibrary.execute_console_command(world,"r.Streaming.FullyLoadUsedTextures 1");unreal.EditorLevelLibrary.editor_set_game_view(True);unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation();unreal.AutomationLibrary.finish_loading_before_screenshot();task=unreal.AutomationLibrary.take_high_res_screenshot(1920,1080,str(out),camera=cam,force_game_view=True,delay=15)
if not task.is_valid_task():raise RuntimeError("invalid screenshot")
started=time.monotonic();handle=None
def done(_):
 global handle
 elapsed=time.monotonic()-started
 if elapsed>=16 and out.exists() and out.stat().st_size>=1024:unreal.log(f"LB_V322_CAPTURE_PASS path={out}")
 elif elapsed<90:return
 else:unreal.log_error("LB_V322_CAPTURE_FAIL")
 if handle is not None:unreal.unregister_slate_post_tick_callback(handle);handle=None
 unreal.EditorPythonScripting.set_keep_python_script_alive(False)
handle=unreal.register_slate_post_tick_callback(done)
