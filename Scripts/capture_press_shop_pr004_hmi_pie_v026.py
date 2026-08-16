"""Capture the real PR-004 world-space HMI from a simulated runtime world."""

import time
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004PackagingPolishCandidate_v026"
OUTPUT = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/PressShopIntegration/v026_pr004_packaging_polish/press_shop_v026_pr004_hmi_pie.png"
CAMERA_TAG = unreal.Name("LB.Capture.PR004HMI.v026")
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

camera = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(-4990.0, -1295.0, 175.0),
                                       unreal.Rotator(roll=0.0, pitch=-4.38, yaw=-146.44))
camera.set_actor_label("LB_PR004_V026_CAM_HMI_PIE_FIXED")
camera.tags = [CAMERA_TAG]
camera.camera_component.set_field_of_view(39.0)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
if OUTPUT.exists():
    OUTPUT.unlink()

unreal.EditorLevelLibrary.editor_play_simulate()
started = time.monotonic()
handle = None


def terminate_failure(message):
    global handle
    unreal.log_error(f"LINE_BOSS_PR004_HMI_PIE_CAPTURE_FAIL {message}")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.SystemLibrary.quit_editor()


def finish_tick(_delta_seconds):
    global handle
    elapsed = time.monotonic() - started
    if elapsed >= 3.0 and OUTPUT.exists() and OUTPUT.stat().st_size >= 1024:
        unreal.log(f"LINE_BOSS_PR004_HMI_PIE_CAPTURE_PASS output={OUTPUT}")
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
    stations = unreal.GameplayStatics.get_all_actors_of_class(game_world, unreal.LBPR004Station)
    cameras = unreal.GameplayStatics.get_all_actors_with_tag(game_world, CAMERA_TAG)
    if not stations or not cameras:
        return
    # Prevent the screenshot request from re-entering preparation while it
    # pumps Slate internally.
    unreal.unregister_slate_post_tick_callback(handle)
    handle = None
    try:
        station = stations[0]
        runtime_camera = cameras[0]
        power_ok = station.set_control_power(True)
        commission_ok = station.set_cell_commissioned(True)
        coil_id = station.get_current_coil_id()
        load_ok = True
        if not coil_id:
            coil_id = "MCX-U-V026-PIE"
            load_ok = station.load_packaged_coil(coil_id)
        recipe_ok = station.select_depack_recipe(unreal.Name("PR004_DEPACK_STANDARD"), coil_id)
        steps = [power_ok, commission_ok, load_ok, recipe_ok,
                 station.set_cradle_locked(True), station.set_c_hook_withdrawn(True)]
        if not all(steps):
            terminate_failure(f"authority={steps} coil={coil_id}")
            return
        widget_components = {component.get_name(): component for component in station.get_components_by_class(unreal.WidgetComponent)}
        operator_hmi = widget_components.get("PR004_OperatorHMI")
        widget = operator_hmi.get_user_widget_object() if operator_hmi is not None else None
        if widget is None:
            terminate_failure(f"widget={sorted(widget_components)}")
            return
        widget.bind_station(station)
        unreal.log(
            "LINE_BOSS_PR004_HMI_PIE_WIDGET "
            + f"component_visible={operator_hmi.is_visible()} click_collision={operator_hmi.get_collision_enabled()}"
        )
        unreal.SystemLibrary.execute_console_command(game_world, "viewmode lit")
        unreal.SystemLibrary.execute_console_command(game_world, "r.Streaming.FullyLoadUsedTextures 1")
        unreal.SystemLibrary.execute_console_command(game_world, "r.HighResScreenshotDelay 28")
        unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
        unreal.AutomationLibrary.finish_loading_before_screenshot()
        task = unreal.AutomationLibrary.take_high_res_screenshot(
            1920, 1080, str(OUTPUT), camera=runtime_camera, force_game_view=True)
        if not task.is_valid_task():
            terminate_failure("invalid_task")
            return
        unreal.log("LINE_BOSS_PR004_HMI_PIE_RUNTIME_READY")
        handle = unreal.register_slate_post_tick_callback(finish_tick)
    except Exception as exc:
        terminate_failure(f"exception={exc}")


handle = unreal.register_slate_post_tick_callback(start_tick)
