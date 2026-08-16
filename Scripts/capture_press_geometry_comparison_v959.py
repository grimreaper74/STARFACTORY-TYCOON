"""Capture the isolated same-height old/high-resolution press comparison."""
import time
from pathlib import Path
import unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
map_path = "/Game/LineBoss/Developer/Validation/Maps/LB_PressGeometryComparison_v958"
output = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/PressShop/PressGeometry_v960/old_vs_highres_press_neutral.png"
tag = unreal.Name("LB.Capture.PressGeometry.v960")
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(map_path):
    raise RuntimeError(map_path)
camera = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(1700, -1850, 980))
camera.tags = [tag]
camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(), unreal.Vector(0, 0, 390)), False)
camera.camera_component.set_field_of_view(64)
output.parent.mkdir(parents=True, exist_ok=True)
if output.exists():
    output.unlink()
unreal.EditorLevelLibrary.editor_play_simulate()
start = time.monotonic()
shot_at = None
handle = None

def finish(ok, message):
    global handle
    (unreal.log if ok else unreal.log_error)(f"LINE_BOSS_PRESS_GEOMETRY_CAPTURE_V959_{'PASS' if ok else 'FAIL'} {message}")
    if handle:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.SystemLibrary.quit_editor()

def tick(_dt):
    global shot_at
    now = time.monotonic()
    world = unreal.EditorLevelLibrary.get_game_world()
    if not world:
        return
    cameras = unreal.GameplayStatics.get_all_actors_with_tag(world, tag)
    if shot_at is None and now - start > 8 and cameras:
        unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
        unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
        unreal.AutomationLibrary.finish_loading_before_screenshot()
        task = unreal.AutomationLibrary.take_high_res_screenshot(2560, 1440, str(output), camera=cameras[0], force_game_view=True)
        if not task.is_valid_task():
            finish(False, "invalid screenshot task")
            return
        shot_at = now
    elif shot_at is not None and output.exists() and output.stat().st_size > 1024:
        finish(True, str(output))
    elif now - start > 100:
        finish(False, "timeout")

handle = unreal.register_slate_post_tick_callback(tick)
