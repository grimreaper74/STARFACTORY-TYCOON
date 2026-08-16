import time
from pathlib import Path
import unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP = "/Game/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913"
OUT = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/PressShop/PlayerBuildable_v916/player_built_approved_lorry.png"
TAG = unreal.Name("LB.Capture.PlayerBuiltLorry.v916")
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)

lorry = actors.spawn_actor_from_class(unreal.LBFactoryBuildMachine, unreal.Vector(0.0, 0.0, 0.0))
if not lorry.configure("INBOUND-001", unreal.LBFactoryBuildMachineType.INBOUND_DELIVERY_DOCK):
    raise RuntimeError("Could not configure approved inbound lorry")

camera = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(-2500.0, -3000.0, 1800.0))
camera.set_actor_label("LB_CAPTURE_PlayerBuiltLorry_v916_NOT_SAVED")
camera.tags = [TAG]
camera.set_actor_rotation(
    unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(), unreal.Vector(0.0, 0.0, 170.0)), False)
camera.camera_component.set_field_of_view(52.0)

OUT.parent.mkdir(parents=True, exist_ok=True)
if OUT.exists():
    OUT.unlink()
unreal.EditorLevelLibrary.editor_play_simulate()
started = time.monotonic()
capture_started = None
handle = None

def finish(ok, detail):
    global handle
    (unreal.log if ok else unreal.log_error)(f"LINE_BOSS_PLAYER_BUILT_LORRY_V916_{'PASS' if ok else 'FAIL'} {detail}")
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
    runtime_cameras = unreal.GameplayStatics.get_all_actors_with_tag(world, TAG)
    runtime_lorries = [a for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBFactoryBuildMachine)
                       if a.get_machine_type() == unreal.LBFactoryBuildMachineType.INBOUND_DELIVERY_DOCK]
    if capture_started is None and now - started >= 5.0 and runtime_cameras and runtime_lorries:
        visual = runtime_lorries[0].get_approved_visual_component()
        unreal.log(f"LINE_BOSS_PLAYER_BUILT_LORRY_V916_RUNTIME mesh={visual.static_mesh} extent={runtime_lorries[0].get_machine_half_extent()}")
        unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
        unreal.AutomationLibrary.finish_loading_before_screenshot()
        task = unreal.AutomationLibrary.take_high_res_screenshot(
            1600, 900, str(OUT), camera=runtime_cameras[0], force_game_view=True)
        if not task.is_valid_task():
            finish(False, "invalid screenshot task")
            return
        capture_started = now
    elif capture_started is not None and OUT.exists() and OUT.stat().st_size >= 1024:
        finish(True, str(OUT))
    elif now - started > 75.0:
        finish(False, "timeout")

handle = unreal.register_slate_post_tick_callback(tick)
