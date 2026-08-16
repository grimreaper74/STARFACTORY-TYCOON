"""Capture one fixed-camera v300 balanced Train A view."""

import os
import time
from pathlib import Path
import unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP = "/Game/LineBoss/Maps/LB_PressShop_TrainABalancedLightingCandidate_v300"
CAPTURES = {
    "operator": ("LB_V300_CAM_TrainAOperatorInsideGrid", "v300_train_a_operator.png"),
    "fabrication": ("LB_V300_CAM_TrainAFabricationInsideGrid", "v300_train_a_fabrication.png"),
    "overview": ("LB_V300_CAM_TrainAHighInsideGrid", "v300_train_a_overview.png"),
}
capture_id = os.environ.get("LB_V300_CAPTURE", "operator").lower()
label, filename = CAPTURES[capture_id]
output = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/PressShopIntegration/v300_train_a_balanced_lighting" / filename
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
camera = next((actor for actor in api.get_all_level_actors() if actor.get_actor_label() == label), None)
if camera is None:
    raise RuntimeError(label)
output.parent.mkdir(parents=True, exist_ok=True)
if output.exists():
    output.unlink()
world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
unreal.SystemLibrary.execute_console_command(world, "r.HighResScreenshotDelay 24")
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()
task = unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, str(output), camera=camera, mask_enabled=False, capture_hdr=False, comparison_tolerance=unreal.ComparisonTolerance.LOW, comparison_notes=f"Cairnwell v300 balanced Train A {capture_id}", delay=0, force_game_view=True)
if not task.is_valid_task():
    raise RuntimeError("invalid screenshot task")
started = time.monotonic()
handle = None

def finish(_delta):
    global handle
    elapsed = time.monotonic() - started
    if elapsed >= 3 and output.exists() and output.stat().st_size >= 1024:
        unreal.log(f"LB_V300_CAPTURE_PASS id={capture_id} path={output}")
    elif elapsed < 70:
        return
    else:
        unreal.log_error(f"LB_V300_CAPTURE_FAIL id={capture_id} path={output}")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)

handle = unreal.register_slate_post_tick_callback(finish)
