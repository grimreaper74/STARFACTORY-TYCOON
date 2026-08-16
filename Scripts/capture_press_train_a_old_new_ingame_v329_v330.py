"""Capture either matched old or new Train A whole-shop child."""
import os
import time
from pathlib import Path
import unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
variant = os.environ.get("LB_TRAIN_A_INGAME_VARIANT", "old").lower()
if variant == "old":
    map_path = "/Game/LineBoss/Maps/LB_PressShop_TrainAOldInGameReview_v329"
    label = "LB_V329_CAM_TRAIN_A_MATCHED_INGAME"
else:
    map_path = "/Game/LineBoss/Maps/LB_PressShop_TrainANewInGameReview_v330"
    label = "LB_V330_CAM_TRAIN_A_MATCHED_INGAME"
out = Path(unreal.Paths.project_saved_dir()) / f"ValidationScreenshots/PressShopIntegration/v330_train_a_old_new_ingame/train_a_{variant}_ingame.png"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(map_path):
    raise RuntimeError(map_path)
cam = next((a for a in actors.get_all_level_actors() if a.get_actor_label() == label), None)
if cam is None:
    raise RuntimeError(label)
out.parent.mkdir(parents=True, exist_ok=True)
if out.exists():
    raise RuntimeError(f"Refusing to overwrite {out}")
world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()
task = unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, str(out), camera=cam, force_game_view=True, delay=15)
if not task.is_valid_task():
    raise RuntimeError("Invalid screenshot task")
started = time.monotonic()
handle = None
def done(_):
    global handle
    elapsed = time.monotonic() - started
    if elapsed >= 16 and out.exists() and out.stat().st_size >= 1024:
        unreal.log(f"LB_TRAIN_A_INGAME_CAPTURE_PASS variant={variant} path={out}")
    elif elapsed < 90:
        return
    else:
        unreal.log_error(f"LB_TRAIN_A_INGAME_CAPTURE_FAIL variant={variant}")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
handle = unreal.register_slate_post_tick_callback(done)
