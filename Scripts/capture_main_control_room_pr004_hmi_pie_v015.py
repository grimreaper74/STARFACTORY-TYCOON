"""Capture the live control-room PR-004 HMI after its render target has painted."""

import math
import time
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_MainControlRoom_PR004LiveSurfaceCandidate_v015"
OUTPUT = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/ControlRoom/v015_pr004_live_hmi/main_control_room_v015_pr004_hmi_pie.png"
CAMERA_TAG = unreal.Name("LB.Capture.ControlRoom.PR004HMI.v015")
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

seat = unreal.Vector(0.0, 82.0, 112.0)
target = unreal.Vector(-182.805, -90.047, 147.337)
direction = target - seat
horizontal = math.sqrt(direction.x * direction.x + direction.y * direction.y)
yaw = math.degrees(math.atan2(direction.y, direction.x))
pitch = math.degrees(math.atan2(direction.z, horizontal))
camera = actors.spawn_actor_from_class(
    unreal.CameraActor,
    seat,
    unreal.Rotator(pitch=pitch, yaw=yaw, roll=0.0),
)
camera.set_actor_label("LB_MCR_V015_CAM_PR004_HMI_PIE_FIXED")
camera.tags = [CAMERA_TAG]
camera.camera_component.set_field_of_view(60.0)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
if OUTPUT.exists():
    OUTPUT.unlink()
unreal.EditorLevelLibrary.editor_play_simulate()
started = time.monotonic()
handle = None


def terminate_failure(message):
    global handle
    unreal.log_error(f"LINE_BOSS_MCR_PR004_HMI_PIE_CAPTURE_FAIL {message}")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.SystemLibrary.quit_editor()


def finish_tick(_delta_seconds):
    global handle
    elapsed = time.monotonic() - started
    if elapsed >= 3.0 and OUTPUT.exists() and OUTPUT.stat().st_size >= 1024:
        unreal.log(f"LINE_BOSS_MCR_PR004_HMI_PIE_CAPTURE_PASS output={OUTPUT}")
    elif elapsed < 70.0:
        return
    else:
        terminate_failure("timeout")
        return
    unreal.unregister_slate_post_tick_callback(handle)
    handle = None
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.SystemLibrary.quit_editor()


def start_tick(_delta_seconds):
    global handle
    game_world = unreal.EditorLevelLibrary.get_game_world()
    if game_world is None:
        return
    consoles = unreal.GameplayStatics.get_all_actors_of_class(game_world, unreal.LBControlRoomPR004Console)
    cameras = unreal.GameplayStatics.get_all_actors_with_tag(game_world, CAMERA_TAG)
    if not consoles or not cameras:
        return
    unreal.unregister_slate_post_tick_callback(handle)
    handle = None
    try:
        console = consoles[0]
        runtime_camera = cameras[0]
        station = console.get_bound_station()
        components = {component.get_name(): component for component in console.get_components_by_class(unreal.WidgetComponent)}
        operator_hmi = components.get("PR004ControlRoomScreen")
        widget = operator_hmi.get_user_widget_object() if operator_hmi is not None else None
        if station is None or widget is None:
            terminate_failure(f"station={station} components={sorted(components)} widget={widget}")
            return
        widget.bind_station(station)
        unreal.log(
            "LINE_BOSS_MCR_PR004_HMI_PIE_WIDGET "
            + f"station={station.get_name()} state={station.get_process_state()} "
            + f"visible={operator_hmi.is_visible()} collision={operator_hmi.get_collision_enabled()}"
        )
        unreal.SystemLibrary.execute_console_command(game_world, "viewmode lit")
        unreal.SystemLibrary.execute_console_command(game_world, "r.Streaming.FullyLoadUsedTextures 1")
        unreal.SystemLibrary.execute_console_command(game_world, "r.HighResScreenshotDelay 32")
        unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
        unreal.AutomationLibrary.finish_loading_before_screenshot()
        task = unreal.AutomationLibrary.take_high_res_screenshot(
            1920, 1080, str(OUTPUT), camera=runtime_camera, force_game_view=True
        )
        if not task.is_valid_task():
            terminate_failure("invalid_task")
            return
        unreal.log("LINE_BOSS_MCR_PR004_HMI_PIE_RUNTIME_READY")
        handle = unreal.register_slate_post_tick_callback(finish_tick)
    except Exception as exc:
        terminate_failure(f"exception={exc}")


handle = unreal.register_slate_post_tick_callback(start_tick)
