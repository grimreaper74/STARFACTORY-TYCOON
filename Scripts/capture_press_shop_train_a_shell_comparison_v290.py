"""Capture one inherited-hall v290 shell comparison per clean process."""
import os,time
from pathlib import Path
import unreal
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP="/Game/LineBoss/Maps/LB_PressShop_TrainAShellComparisonCandidate_v290"
CAPTURES={"operator":("LB_V290_CAM_TrainAOperatorShell","v290_train_a_operator_shell.png"),"close":("LB_V290_CAM_TrainAShellClose","v290_train_a_shell_close.png"),"management":("LB_V290_CAM_TrainAShellManagement","v290_train_a_shell_management.png")}
cid=os.environ.get("LB_V290_CAPTURE","operator").lower()
if cid not in CAPTURES:raise RuntimeError(cid)
label,filename=CAPTURES[cid];output=Path(unreal.Paths.project_saved_dir())/"ValidationScreenshots/PressShopIntegration/v290_train_a_shell"/filename
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);api=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):raise RuntimeError(MAP)
cam=next((a for a in api.get_all_level_actors() if a.get_actor_label()==label),None)
if cam is None:raise RuntimeError(label)
output.parent.mkdir(parents=True,exist_ok=True)
if output.exists():output.unlink()
world=unreal.EditorLevelLibrary.get_editor_world();unreal.SystemLibrary.execute_console_command(world,"viewmode lit");unreal.SystemLibrary.execute_console_command(world,"r.Streaming.FullyLoadUsedTextures 1");unreal.SystemLibrary.execute_console_command(world,"r.HighResScreenshotDelay 24");unreal.EditorLevelLibrary.editor_set_game_view(True);unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation();unreal.AutomationLibrary.finish_loading_before_screenshot()
task=unreal.AutomationLibrary.take_high_res_screenshot(1920,1080,str(output),camera=cam,mask_enabled=False,capture_hdr=False,comparison_tolerance=unreal.ComparisonTolerance.LOW,comparison_notes=f"Cairnwell v290 inherited-hall Train A shell {cid}",delay=0,force_game_view=True)
if not task.is_valid_task():raise RuntimeError("invalid screenshot task")
started=time.monotonic();handle=None
def finish(_delta):
 global handle
 e=time.monotonic()-started
 if e>=3 and output.exists() and output.stat().st_size>=1024:unreal.log(f"LB_V290_CAPTURE_PASS id={cid} path={output}")
 elif e<65:return
 else:unreal.log_error(f"LB_V290_CAPTURE_FAIL id={cid} path={output}")
 if handle is not None:unreal.unregister_slate_post_tick_callback(handle);handle=None
 unreal.EditorPythonScripting.set_keep_python_script_alive(False)
handle=unreal.register_slate_post_tick_callback(finish)
