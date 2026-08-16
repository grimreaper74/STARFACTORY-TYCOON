"""Capture corrected support-robot material preview v003 from its direct map."""

from pathlib import Path
import time

import unreal


MAP = "/Game/LineBoss/Developer/Validation/LB_SupportRobot_Materials_Candidate_v003"
CAMERA = "LB_CAM_SupportRobot_MaterialPreview_v003"
OUTPUT = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/SupportRobots/Materials/Candidate_v003/lb_support_robot_materials_v003.png"
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
world = unreal.EditorLevelLibrary.get_editor_world()
current_package = world.get_outermost().get_name() if world is not None else ""
if current_package != MAP:
    raise RuntimeError(f"One-map rule violation: opened {current_package}, expected {MAP}")
camera = next((actor for actor in actors.get_all_level_actors() if actor.get_actor_label() == CAMERA), None)
if camera is None:
    raise RuntimeError(f"Missing fixed camera {CAMERA}")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
if OUTPUT.exists():
    OUTPUT.unlink()
unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
unreal.SystemLibrary.execute_console_command(world, "r.HighResScreenshotDelay 20")
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()
task = unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, str(OUTPUT), camera=camera, force_game_view=True)
if not task.is_valid_task():
    raise RuntimeError("Invalid v003 material-preview screenshot task")
started = time.monotonic()
handle = None


def finish(_delta):
    global handle
    elapsed = time.monotonic() - started
    if elapsed >= 3.0 and OUTPUT.exists() and OUTPUT.stat().st_size >= 1024:
        unreal.log(f"LINE_BOSS_SUPPORT_ROBOT_MATERIAL_PREVIEW_V003_CAPTURE_PASS path={OUTPUT}")
    elif elapsed < 55.0:
        return
    else:
        unreal.log_error(f"LINE_BOSS_SUPPORT_ROBOT_MATERIAL_PREVIEW_V003_CAPTURE_FAIL path={OUTPUT}")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.SystemLibrary.quit_editor()


handle = unreal.register_slate_post_tick_callback(finish)
