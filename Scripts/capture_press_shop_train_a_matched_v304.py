"""Capture one corrected, Pro-matched Train A v304 review view."""
import os
import time
from pathlib import Path

import unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP = "/Game/LineBoss/Maps/LB_PressShop_TrainACorrectedReviewCandidate_v304"
CAPTURES = {
    "operator": ("LB_V304_CAM_TrainAOperatorMatched", "v304_train_a_operator_matched.png"),
    "rear": ("LB_V304_CAM_TrainARearMatched", "v304_train_a_rear_matched.png"),
    "elevated": ("LB_V304_CAM_TrainAElevatedMatched", "v304_train_a_elevated_matched.png"),
}
capture_id = os.environ.get("LB_V304_CAPTURE", "operator").lower()
label, filename = CAPTURES[capture_id]
output = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/PressShopIntegration/v304_train_a_matched" / filename
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
camera = next((a for a in actors_api.get_all_level_actors() if a.get_actor_label() == label), None)
if camera is None:
    raise RuntimeError(label)
# Editor high-resolution screenshots do not consistently respect HiddenInGame.
# Apply transient editor hiding here so retained native Train A geometry is not
# superimposed over the isolated v037 candidate. Nothing is saved to the map.
for actor in actors_api.get_all_level_actors():
    tags = {str(t) for t in actor.tags}
    actor_label = actor.get_actor_label()
    legacy_train_a = (
        actor_label.startswith("LB_INST_PTA_")
        or "LB.PressTrain.Installed.TRAIN_A" in tags
        or actor_label == "LB_V300_PTA_SEGMENTED_BALANCED_SHELL"
    )
    review_obstruction = actor_label in {
        "LB_PRESS_Column_2000_-5250", "LB_PRESS_Column_4000_-5250",
        "LB_PRESS_Column_2000_-3750", "LB_PRESS_Column_4000_-3750",
        "LB_V301_WIDESPAN_TRANSFER_GIRDER_X6000_Y-5250_TBC",
        "LB_V301_WIDESPAN_TRANSFER_GIRDER_X6000_Y-3750_TBC",
    }
    if actor != camera and (legacy_train_a or review_obstruction):
        actor.set_is_temporarily_hidden_in_editor(True)
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
    comparison_notes=f"Cairnwell v304 corrected Train A {capture_id}", delay=0, force_game_view=True,
)
if not task.is_valid_task():
    raise RuntimeError("invalid screenshot task")
started = time.monotonic()
handle = None
def finish(_delta):
    global handle
    elapsed = time.monotonic() - started
    if elapsed >= 3 and output.exists() and output.stat().st_size >= 1024:
        unreal.log(f"LB_V304_CAPTURE_PASS id={capture_id} path={output}")
    elif elapsed < 70:
        return
    else:
        unreal.log_error(f"LB_V304_CAPTURE_FAIL id={capture_id} path={output}")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
handle = unreal.register_slate_post_tick_callback(finish)
