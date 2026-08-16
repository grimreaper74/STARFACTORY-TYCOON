"""Capture verified inside-grid broadside evidence for v343 Train A."""
import os
import time
from pathlib import Path
import unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
view = os.environ.get("LB_V349_VIEW", "broadside").lower()
views = {
    "broadside": ((3850.0, -5600.0, 800.0), (3850.0, -4300.0, 430.0), 126.0),
    "elevated": ((3850.0, -5600.0, 1550.0), (3850.0, -4300.0, 360.0), 120.0),
}
if view not in views:
    raise RuntimeError(view)
out = Path(unreal.Paths.project_saved_dir()) / f"ValidationScreenshots/PressShopIntegration/v349_train_a_release_integration/{view}.png"
if out.exists():
    raise RuntimeError(f"Refusing to overwrite {out}")
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level("/Game/LineBoss/Maps/LB_PressShop_TrainAReleaseIntegrationCandidate_v343"):
    raise RuntimeError("v343 load failed")
location, target, fov = views[view]
camera = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(), unreal.Vector(*target)), False)
camera.camera_component.set_editor_properties({"field_of_view": fov, "aspect_ratio": 16.0 / 9.0, "constrain_aspect_ratio": True})
out.parent.mkdir(parents=True, exist_ok=True)
world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()
task = unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, str(out), camera=camera, force_game_view=True, delay=15)
if not task.is_valid_task():
    raise RuntimeError("Invalid v349 task")
started = time.monotonic()
handle = None

def tick(_):
    global handle
    elapsed = time.monotonic() - started
    if elapsed >= 16 and out.exists() and out.stat().st_size >= 1024:
        unreal.log(f"LB_TRAIN_A_V349_CAPTURE_PASS view={view}")
    elif elapsed < 90:
        return
    else:
        unreal.log_error(f"LB_TRAIN_A_V349_CAPTURE_FAIL view={view}")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.execute_console_command(world, "QUIT_EDITOR")

handle = unreal.register_slate_post_tick_callback(tick)
