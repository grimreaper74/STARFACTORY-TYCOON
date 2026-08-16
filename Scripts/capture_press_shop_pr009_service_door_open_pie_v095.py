"""Capture the v095 interlocked service door visibly open in a simulated runtime world."""

import time
from pathlib import Path

import unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)

MAP = "/Game/LineBoss/Maps/LB_PressShop_PR009EnclosureReleaseCandidate_v095"
OUTPUT = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/PressShopIntegration/v095_pr009_enclosure/press_shop_v095_pr009_service_door_open_pie.png"
CAMERA_TAG = unreal.Name("LB.Capture.PR009.v095.ServiceDoorOpen")
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)

location = unreal.Vector(0.0, -2820.0, 400.0)
target = unreal.Vector(550.0, -2020.0, 130.0)
camera = actors.spawn_actor_from_class(unreal.CameraActor, location, unreal.Rotator())
camera.set_actor_label("LB_PR009_V095_CAM_SERVICE_DOOR_OPEN_PIE_FIXED")
camera.tags = [CAMERA_TAG]
camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(location, target), False)
camera.camera_component.set_field_of_view(48.0)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
if OUTPUT.exists(): OUTPUT.unlink()
unreal.EditorLevelLibrary.editor_play_simulate()
started = time.monotonic()
opened_at = None
handle = None


def terminate(message, failure=False):
    global handle
    unreal.log_error(message) if failure else unreal.log(message)
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()


def tick(_delta):
    global opened_at, handle
    elapsed = time.monotonic() - started
    if elapsed >= 70.0:
        terminate("PR009_V095_SERVICE_DOOR_OPEN_PIE_CAPTURE_FAIL timeout", True)
        return
    if OUTPUT.exists() and OUTPUT.stat().st_size >= 1024:
        terminate(f"PR009_V095_SERVICE_DOOR_OPEN_PIE_CAPTURE_PASS output={OUTPUT}")
        return
    world = unreal.EditorLevelLibrary.get_game_world()
    if world is None: return
    stations = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBPR009Station)
    cameras = unreal.GameplayStatics.get_all_actors_with_tag(world, CAMERA_TAG)
    if len(stations) != 1 or len(cameras) != 1: return
    station = stations[0]
    if opened_at is None:
        station.set_guards_closed(False)
        opened_at = time.monotonic()
        return
    if time.monotonic() - opened_at < 1.5: return
    if abs(station.get_service_door_angle_degrees() - 105.0) > 0.1: return
    unreal.unregister_slate_post_tick_callback(handle)
    handle = None
    unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
    unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
    unreal.SystemLibrary.execute_console_command(world, "r.HighResScreenshotDelay 28")
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    unreal.AutomationLibrary.finish_loading_before_screenshot()
    task = unreal.AutomationLibrary.take_high_res_screenshot(
        1920, 1080, str(OUTPUT), camera=cameras[0], force_game_view=True,
        comparison_notes="Cairnwell PR-009 v095 interlocked service door open in PIE")
    if not task.is_valid_task():
        terminate("PR009_V095_SERVICE_DOOR_OPEN_PIE_CAPTURE_FAIL invalid task", True)
        return
    handle = unreal.register_slate_post_tick_callback(tick)


handle = unreal.register_slate_post_tick_callback(tick)
