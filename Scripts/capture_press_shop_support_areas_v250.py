"""Capture one transient fixed view of v250 support areas per clean process."""

import os
import time
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v250"
VIEWS = {
    "north_west": ((-3000.0, 2600.0, 950.0), (-6100.0, 4500.0, 110.0), 53.0),
    "north_centre": ((5400.0, 2600.0, 950.0), (1100.0, 4500.0, 110.0), 58.0),
    "east_support": ((7200.0, 900.0, 1050.0), (9650.0, -1900.0, 110.0), 58.0),
}
capture_id = os.environ.get("LB_V250_SUPPORT_CAPTURE", "north_west").lower()
if capture_id not in VIEWS:
    raise RuntimeError(capture_id)
location, target, fov = VIEWS[capture_id]
output = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/PressShopIntegration/v250_support_areas" / f"v250_{capture_id}.png"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
camera = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
camera.set_actor_label(f"LB_V250_TRANSIENT_CAM_{capture_id}")
camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(), unreal.Vector(*target)), False)
camera.camera_component.set_editor_properties({"field_of_view": fov, "aspect_ratio": 16.0 / 9.0, "constrain_aspect_ratio": True})
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
task = unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, str(output), camera=camera, mask_enabled=False,
    capture_hdr=False, comparison_tolerance=unreal.ComparisonTolerance.LOW,
    comparison_notes=f"Cairnwell Moorcross v250 support areas {capture_id}", delay=0.0, force_game_view=True)
if not task.is_valid_task():
    raise RuntimeError("invalid screenshot task")
started = time.monotonic()
handle = None


def finish(_delta):
    global handle
    elapsed = time.monotonic() - started
    if elapsed >= 3.0 and output.exists() and output.stat().st_size >= 1024:
        unreal.log(f"LB_V250_SUPPORT_CAPTURE_PASS id={capture_id} path={output}")
    elif elapsed < 65.0:
        return
    else:
        unreal.log_error(f"LB_V250_SUPPORT_CAPTURE_FAIL id={capture_id} path={output}")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.SystemLibrary.quit_editor()


handle = unreal.register_slate_post_tick_callback(finish)
