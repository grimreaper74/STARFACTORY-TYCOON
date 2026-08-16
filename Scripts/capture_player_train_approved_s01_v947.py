"""Close Unreal proof of the 52-part approved S01 inside the player-placeable train."""
import time
from pathlib import Path
import unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP = "/Game/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913"
OUT = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/PressShop/PlayerBuildable_v947/player_train_approved_s01.png"
TAG = unreal.Name("LB.Capture.PlayerTrainApprovedS01.v947")
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)

train = actors.spawn_actor_from_class(unreal.LBPressTrainAStation, unreal.Vector(0.0, -4000.0, 0.0))
if not train.configure_train_variant("TRAIN_A", "PRESS TRAIN A", "SMOT / SMOTR / ROOF OUTER", unreal.LinearColor(0.20, 0.55, 0.82, 1)):
    raise RuntimeError("configure failed")
if not train.enable_completed_runtime_visual():
    raise RuntimeError("approved 87-part visual failed")

# S01 occupies the train origin and S02 is 7.5 m downstream on local +Y.
camera = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(-1900.0, -5550.0, 1050.0))
camera.tags = [TAG]
camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
    camera.get_actor_location(), unreal.Vector(0.0, -3650.0, 155.0)), False)
camera.camera_component.set_field_of_view(56.0)
OUT.parent.mkdir(parents=True, exist_ok=True)
if OUT.exists(): OUT.unlink()
unreal.EditorLevelLibrary.editor_play_simulate()
started = time.monotonic()
capture_started = None
handle = None

def finish(ok, detail):
    global handle
    (unreal.log if ok else unreal.log_error)(f"LINE_BOSS_PLAYER_TRAIN_APPROVED_S01_V947_{'PASS' if ok else 'FAIL'} {detail}")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.SystemLibrary.quit_editor()

def tick(_delta):
    global capture_started
    now = time.monotonic()
    world = unreal.EditorLevelLibrary.get_game_world()
    if not world: return
    cameras = unreal.GameplayStatics.get_all_actors_with_tag(world, TAG)
    trains = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBPressTrainAStation)
    if capture_started is None and now - started >= 7.0 and cameras and len(trains) == 1:
        if not trains[0].has_completed_runtime_visual():
            finish(False, "approved visual inactive"); return
        task = unreal.AutomationLibrary.take_high_res_screenshot(2560, 1440, str(OUT), camera=cameras[0], force_game_view=True)
        if not task.is_valid_task():
            finish(False, "invalid screenshot task"); return
        capture_started = now
    elif capture_started is not None and OUT.exists() and OUT.stat().st_size > 1024:
        finish(True, str(OUT))
    elif now - started > 90.0:
        finish(False, "timeout")

handle = unreal.register_slate_post_tick_callback(tick)
