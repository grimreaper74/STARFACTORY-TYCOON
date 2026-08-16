"""Capture one v289 train-presentation camera per clean Unreal process."""

import os
import time
from pathlib import Path

import unreal


unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP = "/Game/LineBoss/Maps/LB_PressShop_TrainPresentationCandidate_v289"
CAPTURES = {
    "train_a": ("LB_V289_CAM_TrainAOperator", "v289_train_a_operator.png"),
    "train_b": ("LB_V289_CAM_TrainBOperator", "v289_train_b_operator.png"),
    "train_cd": ("LB_V289_CAM_TrainCDService", "v289_train_cd_service.png"),
    "diagonal": ("LB_V289_CAM_FourTrainDiagonal", "v289_four_train_diagonal.png"),
}
capture_id = os.environ.get("LB_V289_CAPTURE", "train_a").lower()
if capture_id not in CAPTURES:
    raise RuntimeError(capture_id)
camera_label, filename = CAPTURES[capture_id]
output = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/PressShopIntegration/v289_train_presentation" / filename

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
camera = next((actor for actor in actors_api.get_all_level_actors() if actor.get_actor_label() == camera_label), None)
if camera is None:
    raise RuntimeError(camera_label)
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
task = unreal.AutomationLibrary.take_high_res_screenshot(
    1920, 1080, str(output), camera=camera, mask_enabled=False, capture_hdr=False,
    comparison_tolerance=unreal.ComparisonTolerance.LOW,
    comparison_notes=f"Cairnwell Moorcross v289 train presentation {capture_id}",
    delay=0.0, force_game_view=True,
)
if not task.is_valid_task():
    raise RuntimeError(f"invalid screenshot task for {capture_id}")

started = time.monotonic()
handle = None


def finish(_delta):
    global handle
    elapsed = time.monotonic() - started
    if elapsed >= 3.0 and output.exists() and output.stat().st_size >= 1024:
        unreal.log(f"LB_V289_CAPTURE_PASS id={capture_id} path={output}")
    elif elapsed < 65.0:
        return
    else:
        unreal.log_error(f"LB_V289_CAPTURE_FAIL id={capture_id} path={output}")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)


handle = unreal.register_slate_post_tick_callback(finish)
