"""Capture v285 through the editor viewport rather than Automation screenshot task."""
import os
import shutil
import time
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v285"
CAPTURES = {
    "pr006": "LB_PR006_V208_CAM_ConnectedRelease",
    "pr007": "LB_PR007_V209_CAM_ConnectedRelease",
    "pr008": "LB_PR008_V210_CAM_AuthoredAnchorProcess",
}
capture_id = os.environ.get("LB_V285_VIEWPORT_CAPTURE", "pr006").lower()
camera_label = CAPTURES[capture_id]
saved = Path(unreal.Paths.project_saved_dir())
output = saved / "ValidationScreenshots/PressShopIntegration/v285_complete_cell" / f"v285_{capture_id}_complete_cell_viewport.png"
screenshots = saved / "Screenshots/WindowsEditor"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
camera = next((a for a in actors_api.get_all_level_actors() if a.get_actor_label() == camera_label), None)
if camera is None:
    raise RuntimeError(camera_label)
output.parent.mkdir(parents=True, exist_ok=True)
if output.exists():
    output.unlink()
before = {path.resolve() for path in screenshots.glob("*.png")} if screenshots.exists() else set()
world = unreal.EditorLevelLibrary.get_editor_world()
levels.set_level_viewport_camera_info(camera.get_actor_location(), camera.get_actor_rotation())
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()
unreal.SystemLibrary.execute_console_command(world, "shot")
started = time.monotonic()
handle = None


def finish(_delta):
    global handle
    fresh = [path for path in screenshots.glob("*.png") if path.resolve() not in before]
    if fresh:
        newest = max(fresh, key=lambda path: path.stat().st_mtime)
        shutil.copy2(newest, output)
        unreal.log(f"LB_V285_VIEWPORT_CAPTURE_PASS id={capture_id} path={output}")
    elif time.monotonic() - started < 30.0:
        return
    else:
        unreal.log_error(f"LB_V285_VIEWPORT_CAPTURE_FAIL id={capture_id}")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.SystemLibrary.quit_editor()


handle = unreal.register_slate_post_tick_callback(finish)
