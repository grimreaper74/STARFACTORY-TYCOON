"""Capture the full Press Shop and both LB-CR01 dock placements."""
import os
import time
from pathlib import Path
import unreal

MAP = "/Game/LineBoss/Maps/LB_PressShop_SupportRobotsCandidate_v005"
CAPTURES = {
    "whole": ("LB_CAM_PressShop_ManagementOverview", "press_shop_v005_support_robots_whole.png"),
    "west": ("LB_CAM_PressShop_ManagementOverview", "press_shop_v005_support_robots_west.png"),
    "east": ("LB_CAM_PressShop_ManagementOverview", "press_shop_v005_support_robots_east.png"),
}
capture_id = os.environ.get("LB_PRESS_V005_CAPTURE", "whole")
camera_label, filename = CAPTURES[capture_id]
output = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/PressShopIntegration/v005_support_robots" / filename
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels.load_level(MAP)
camera = next((a for a in actors.get_all_level_actors() if a.get_actor_label() == camera_label), None)
if camera is None: raise RuntimeError(f"Missing camera {camera_label}")
if capture_id in ("west", "east"):
    # Keep the evidence camera inside the south wall.  The original y=-7600
    # position sat outside the building shell and produced an all-black frame.
    location = unreal.Vector(-9000 if capture_id == "west" else 8500, -3800, 1100)
    target = unreal.Vector(-9800 if capture_id == "west" else 9200, -5200, 55)
    camera.set_actor_location(location, False, False)
    camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(location, target), False)
    camera.get_editor_property("camera_component").set_editor_property("field_of_view", 45.0)
output.parent.mkdir(parents=True, exist_ok=True)
if output.exists(): output.unlink()
world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
unreal.SystemLibrary.execute_console_command(world, "r.HighResScreenshotDelay 28")
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()
task = unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, str(output), camera=camera, force_game_view=True)
if not task.is_valid_task(): raise RuntimeError("Invalid screenshot task")
started = time.monotonic(); tick_handle = None
def finish(_delta):
    global tick_handle
    elapsed = time.monotonic() - started
    if elapsed >= 3.0 and output.exists() and output.stat().st_size >= 1024:
        unreal.log(f"LINE_BOSS_PRESS_V005_CAPTURE_PASS id={capture_id} path={output}")
    elif elapsed < 55.0: return
    else: unreal.log_error(f"LINE_BOSS_PRESS_V005_CAPTURE_FAIL id={capture_id}")
    if tick_handle is not None:
        unreal.unregister_slate_post_tick_callback(tick_handle); tick_handle = None
    unreal.SystemLibrary.quit_editor()
tick_handle = unreal.register_slate_post_tick_callback(finish)
