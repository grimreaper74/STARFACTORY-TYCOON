"""Capture one exact-v039 fixed view per clean Unreal process."""
import os,time
from pathlib import Path
import unreal
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP="/Game/LineBoss/Maps/LB_PressTrainAPresentationShellMaterialCandidate_v039"
CAPTURES={"hero":("CA_MW_PTA_CAM_Hero_v009","v039_hero.png"),"operator":("CA_MW_PTA_CAM_OperatorSide_v009","v039_operator.png"),"mechanics":("CA_MW_PTA_CAM_Mechanics_v009","v039_mechanics.png")}
cid=os.environ.get("LB_PTA_V039_CAPTURE","operator").lower()
if cid not in CAPTURES: raise RuntimeError(cid)
label,filename=CAPTURES[cid]; output=Path(unreal.Paths.project_saved_dir())/"ValidationScreenshots/PressTrains/v039_presentation_shell"/filename
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); api=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP): raise RuntimeError(MAP)
camera=next((a for a in api.get_all_level_actors() if a.get_actor_label()==label),None)
if camera is None: raise RuntimeError(label)
output.parent.mkdir(parents=True,exist_ok=True)
if output.exists(): output.unlink()
world=unreal.EditorLevelLibrary.get_editor_world(); unreal.SystemLibrary.execute_console_command(world,"viewmode lit"); unreal.SystemLibrary.execute_console_command(world,"r.Streaming.FullyLoadUsedTextures 1"); unreal.SystemLibrary.execute_console_command(world,"r.HighResScreenshotDelay 24"); unreal.EditorLevelLibrary.editor_set_game_view(True); unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation(); unreal.AutomationLibrary.finish_loading_before_screenshot()
task=unreal.AutomationLibrary.take_high_res_screenshot(1920,1080,str(output),camera=camera,mask_enabled=False,capture_hdr=False,comparison_tolerance=unreal.ComparisonTolerance.LOW,comparison_notes=f"Cairnwell Train A material shell v039 {cid}",delay=0.0,force_game_view=True)
if not task.is_valid_task(): raise RuntimeError("invalid task")
started=time.monotonic(); handle=None
def finish(_delta):
 global handle
 elapsed=time.monotonic()-started
 if elapsed>=3 and output.exists() and output.stat().st_size>=1024: unreal.log(f"LB_PTA_V039_CAPTURE_PASS id={cid} path={output}")
 elif elapsed<65: return
 else: unreal.log_error(f"LB_PTA_V039_CAPTURE_FAIL id={cid} path={output}")
 if handle is not None: unreal.unregister_slate_post_tick_callback(handle); handle=None
 unreal.EditorPythonScripting.set_keep_python_script_alive(False)
handle=unreal.register_slate_post_tick_callback(finish)
