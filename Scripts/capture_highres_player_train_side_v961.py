"""Broadside proof of the lengthened player train using untouched high-resolution presses."""
import time
from pathlib import Path
import unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
map_path = "/Game/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913"
output = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/PressShop/PlayerBuildable_v963/highres_scaled_transfer_player_train_side.png"
tag = unreal.Name("LB.Capture.HighResPlayerTrain.v963")
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(map_path):
    raise RuntimeError(map_path)
train = actors.spawn_actor_from_class(unreal.LBPressTrainAStation, unreal.Vector(0.0, -3400.0, 0.0))
if not train.configure_train_variant("TRAIN_A", "PRESS TRAIN A", "SMOT / SMOTR / ROOF OUTER", unreal.LinearColor(0.20, 0.55, 0.82, 1)):
    raise RuntimeError("configure failed")
if not train.enable_completed_runtime_visual():
    raise RuntimeError("approved visual failed")
camera = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(-6000.0, 0.0, 1250.0))
camera.tags = [tag]
camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(), unreal.Vector(0.0, 0.0, 330.0)), False)
camera.camera_component.set_field_of_view(62.0)
output.parent.mkdir(parents=True, exist_ok=True)
if output.exists():
    output.unlink()
unreal.EditorLevelLibrary.editor_play_simulate()
started = time.monotonic()
capture_started = None
handle = None

def finish(ok, detail):
    global handle
    (unreal.log if ok else unreal.log_error)(f"LINE_BOSS_HIGHRES_PLAYER_TRAIN_V961_{'PASS' if ok else 'FAIL'} {detail}")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.SystemLibrary.quit_editor()

def tick(_delta):
    global capture_started
    now = time.monotonic()
    world = unreal.EditorLevelLibrary.get_game_world()
    if not world:
        return
    cameras = unreal.GameplayStatics.get_all_actors_with_tag(world, tag)
    trains = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBPressTrainAStation)
    if capture_started is None and now - started >= 10 and cameras and len(trains) == 1:
        if not trains[0].has_completed_runtime_visual():
            finish(False, "approved visual inactive")
            return
        unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
        unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
        unreal.AutomationLibrary.finish_loading_before_screenshot()
        task = unreal.AutomationLibrary.take_high_res_screenshot(2560, 1440, str(output), camera=cameras[0], force_game_view=True)
        if not task.is_valid_task():
            finish(False, "invalid screenshot task")
            return
        capture_started = now
    elif capture_started is not None and output.exists() and output.stat().st_size > 1024:
        finish(True, str(output))
    elif now - started > 110:
        finish(False, "timeout")

handle = unreal.register_slate_post_tick_callback(tick)
