"""Capture clean matched whole-shop old/new Train A views from retained wide camera."""
import os
import time
from pathlib import Path
import unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
variant = os.environ.get("LB_TRAIN_A_INGAME_VARIANT", "old").lower()
exit_when_done = os.environ.get("LB_CAPTURE_EXIT_WHEN_DONE", "0") == "1"
map_path = "/Game/LineBoss/Maps/LB_PressShop_TrainAWideSpanClearanceCandidate_v301" if variant == "old" else "/Game/LineBoss/Maps/LB_PressShop_TrainANewInGameReview_v330"
camera_label = "LB_V295_CAM_TrainAOverview"
out = Path(unreal.Paths.project_saved_dir()) / f"ValidationScreenshots/PressShopIntegration/v333_train_a_old_new_ingame_wide/train_a_{variant}_ingame_wide.png"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(map_path):
    raise RuntimeError(map_path)
all_actors = actors_api.get_all_level_actors()
cam = next((a for a in all_actors if a.get_actor_label() == camera_label), None)
if cam is None:
    raise RuntimeError(camera_label)
if variant == "new":
    for actor in all_actors:
        if actor.get_actor_label() == "CA_MW_PTA_ReadableLabels_v040_WHOLE_SHOP_VISUAL_ONLY_v330":
            actor.set_is_temporarily_hidden_in_editor(False)
            continue
        tags = {str(t) for t in actor.tags}
        label = actor.get_actor_label().upper()
        if "LB.PressTrain.Installed.TRAIN_A" in tags or label.startswith("LB_INST_PTA_"):
            actor.set_is_temporarily_hidden_in_editor(True)
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
        unreal.log(f"LB_TRAIN_A_WIDE_INGAME_CAPTURE_PASS variant={variant} path={out}")
    elif elapsed < 90:
        return
    else:
        unreal.log_error(f"LB_TRAIN_A_WIDE_INGAME_CAPTURE_FAIL variant={variant}")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    if exit_when_done:
        unreal.SystemLibrary.execute_console_command(world, "QUIT_EDITOR")
handle = unreal.register_slate_post_tick_callback(done)
