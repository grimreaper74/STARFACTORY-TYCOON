"""Capture one isolated Train A v307 import-orientation review."""
import os
import time
from pathlib import Path
import unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP = "/Game/LineBoss/Maps/LB_PressTrainA_IsolatedStudioCandidate_v307"
CAPTURES = {
    "operator": ("LB_V307_CAM_Operator", "v307_train_a_operator.png"),
    "rear": ("LB_V307_CAM_Rear", "v307_train_a_rear.png"),
    "elevated": ("LB_V307_CAM_Elevated", "v307_train_a_elevated.png"),
}
capture_id = os.environ.get("LB_V307_CAPTURE", "operator").lower()
label, filename = CAPTURES[capture_id]
output = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/PressShopIntegration/v307_train_a_isolated_studio" / filename
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
camera = next((a for a in api.get_all_level_actors() if a.get_actor_label() == label), None)
if camera is None:
    raise RuntimeError(label)
output.parent.mkdir(parents=True, exist_ok=True)
if output.exists(): output.unlink()
world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
unreal.SystemLibrary.execute_console_command(world, "r.HighResScreenshotDelay 24")
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()
task = unreal.AutomationLibrary.take_high_res_screenshot(1920,1080,str(output),camera=camera,mask_enabled=False,capture_hdr=False,comparison_tolerance=unreal.ComparisonTolerance.LOW,comparison_notes=f"Train A v307 isolated {capture_id}",delay=0,force_game_view=True)
if not task.is_valid_task(): raise RuntimeError("invalid screenshot task")
started=time.monotonic(); handle=None
def finish(_delta):
    global handle
    elapsed=time.monotonic()-started
    if elapsed>=3 and output.exists() and output.stat().st_size>=1024: unreal.log(f"LB_V307_CAPTURE_PASS id={capture_id} path={output}")
    elif elapsed<70: return
    else: unreal.log_error(f"LB_V307_CAPTURE_FAIL id={capture_id} path={output}")
    if handle is not None: unreal.unregister_slate_post_tick_callback(handle); handle=None
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
handle=unreal.register_slate_post_tick_callback(finish)
