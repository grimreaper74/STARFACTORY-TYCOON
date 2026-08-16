"""Fresh fixed-camera PIE evidence for CR-30-01 parked and on-station states."""

import os
import time
from pathlib import Path

import unreal


unreal.EditorPythonScripting.set_keep_python_script_alive(True)


MODE = os.environ.get("LB_SUPPORT_CRANE_CAPTURE", "park").lower()
CANDIDATE = os.environ.get("LB_SUPPORT_CRANE_CANDIDATE", "v036").lower()
DIAGNOSTIC_LIGHT_LABELS = tuple(
    value.strip() for value in os.environ.get(
        "LB_SUPPORT_CRANE_DISABLE_LIGHT_LABELS", "").split("|") if value.strip())
DIAGNOSTIC_SUFFIX = os.environ.get("LB_SUPPORT_CRANE_DIAGNOSTIC_SUFFIX", "").strip()
MAPS = {
    "v036": "/Game/LineBoss/Maps/LB_PressShop_PR004SupportCraneCandidate_v036",
    "v037": "/Game/LineBoss/Maps/LB_PressShop_PR004SupportHookCandidate_v037",
    "v038": "/Game/LineBoss/Maps/LB_PressShop_PR004SupportHookCandidate_v038",
    "v109": "/Game/LineBoss/Maps/LB_PressShop_PR004SupportHoistCandidate_v109",
    "v110": "/Game/LineBoss/Maps/LB_PressShop_PR004SupportIdentityCandidate_v110",
    "v111": "/Game/LineBoss/Maps/LB_PressShop_PR004SupportIdentityCandidate_v111",
    "v112": "/Game/LineBoss/Maps/LB_PressShop_PR004SupportIdentityCandidate_v112",
    "v113": "/Game/LineBoss/Maps/LB_PressShop_PR004SupportIdentityCandidate_v113",
    "v116": "/Game/LineBoss/Maps/LB_PressShop_PR004CarryContextCandidate_v116",
    "v117": "/Game/LineBoss/Maps/LB_PressShop_PR004ConcreteFloorCandidate_v117",
    "v118": "/Game/LineBoss/Maps/LB_PressShop_PR004WrapResponseCandidate_v118",
    "v119": "/Game/LineBoss/Maps/LB_PressShop_PR004HallFinishCandidate_v119",
    "v120": "/Game/LineBoss/Maps/LB_PressShop_PR004HallFinishCandidate_v120",
    "v121": "/Game/LineBoss/Maps/LB_PressShop_PR004HallFinishCandidate_v121",
    "v122": "/Game/LineBoss/Maps/LB_PressShop_PR004HallFinishCandidate_v122",
    "v123": "/Game/LineBoss/Maps/LB_PressShop_PR004HallFinishCandidate_v123",
    "v124": "/Game/LineBoss/Maps/LB_PressShop_PR003Sheet2LayoutCandidate_v124",
    "v125": "/Game/LineBoss/Maps/LB_PressShop_PR004HallFinishCandidate_v125",
    "v126": "/Game/LineBoss/Maps/LB_PressShop_PR004HallFinishCandidate_v126",
    "v127": "/Game/LineBoss/Maps/LB_PressShop_PR004HallFinishCandidate_v127",
    "v128": "/Game/LineBoss/Maps/LB_PressShop_PR004HallLightDiagnostic_v128",
    "v129": "/Game/LineBoss/Maps/LB_PressShop_PR004TaskSpotDiagnostic_v129",
    "v130": "/Game/LineBoss/Maps/LB_PressShop_PR004HallFinishCandidate_v130",
    "v131": "/Game/LineBoss/Maps/LB_PressShop_PR004HallFinishCandidate_v131",
    "v132": "/Game/LineBoss/Maps/LB_PressShop_PR004HallFinishCandidate_v132",
}
VIEWS_V036 = {
    "park": (
        "LB_PR004_V036_CAM_SupportParkSouthInterior",
        "press_shop_v036_support_crane_park_runtime.png"),
    "on_station": (
        "LB_PR004_V036_CAM_SupportOnStationSouthInterior",
        "press_shop_v036_support_crane_on_station_runtime.png"),
}
VIEWS_V037 = {
    "park": (
        "LB_PR004_V037_CAM_SupportParkIdentity",
        "press_shop_v037_support_crane_park_runtime.png"),
    "on_station": (
        "LB_PR004_V037_CAM_SupportOnStationIdentity",
        "press_shop_v037_support_crane_on_station_runtime.png"),
    "hook_close": (
        "LB_PR004_V037_CAM_SupportHookClose",
        "press_shop_v037_support_hook_close_runtime.png"),
}
VIEWS_V038 = {
    "park": (
        "LB_PR004_V038_CAM_SupportParkIdentity",
        "press_shop_v038_support_crane_park_runtime.png"),
    "on_station": (
        "LB_PR004_V038_CAM_SupportOnStationClear",
        "press_shop_v038_support_crane_on_station_runtime.png"),
    "hook_close": (
        "LB_PR004_V038_CAM_SupportHookGuardClose",
        "press_shop_v038_support_hook_guard_close_runtime.png"),
}
VIEWS_V109 = {
    "park": (
        "LB_PR004_V109_CAM_SupportHoistParkClose",
        "press_shop_v109_support_hoist_park_close_runtime.png"),
    "on_station": (
        "LB_PR004_V109_CAM_SupportHoistOnStationClose",
        "press_shop_v109_support_hoist_on_station_close_runtime.png"),
    "fleet": (
        "LB_PR004_V109_CAM_SupportFleetIdentity",
        "press_shop_v109_support_crane_fleet_identity_runtime.png"),
}
VIEWS_V110 = {
    "park": (
        "LB_PR004_V109_CAM_SupportHoistParkClose",
        "press_shop_v110_support_hoist_park_close_runtime.png"),
    "on_station": (
        "LB_PR004_V109_CAM_SupportHoistOnStationClose",
        "press_shop_v110_support_hoist_on_station_close_runtime.png"),
    "fleet": (
        "LB_PR004_V110_CAM_SupportFleetIdentityReadable",
        "press_shop_v110_support_crane_fleet_identity_readable_runtime.png"),
}
VIEWS_V111 = {
    "park": (
        "LB_PR004_V109_CAM_SupportHoistParkClose",
        "press_shop_v111_support_hoist_park_close_runtime.png"),
    "on_station": (
        "LB_PR004_V109_CAM_SupportHoistOnStationClose",
        "press_shop_v111_support_hoist_on_station_close_runtime.png"),
    "fleet": (
        "LB_PR004_V111_CAM_SupportFleetIdentityReadable",
        "press_shop_v111_support_crane_fleet_identity_readable_runtime.png"),
}
VIEWS_V112 = {
    "park": (
        "LB_PR004_V109_CAM_SupportHoistParkClose",
        "press_shop_v112_support_hoist_park_close_runtime.png"),
    "on_station": (
        "LB_PR004_V109_CAM_SupportHoistOnStationClose",
        "press_shop_v112_support_hoist_on_station_close_runtime.png"),
    "fleet": (
        "LB_PR004_V112_CAM_SupportFleetIdentityReadable",
        "press_shop_v112_support_crane_fleet_identity_readable_runtime.png"),
}
VIEWS_V113 = {
    "park": (
        "LB_PR004_V109_CAM_SupportHoistParkClose",
        "press_shop_v113_support_hoist_park_close_runtime.png"),
    "on_station": (
        "LB_PR004_V109_CAM_SupportHoistOnStationClose",
        "press_shop_v113_support_hoist_on_station_close_runtime.png"),
    "fleet": (
        "LB_PR004_V113_CAM_SupportFleetIdentityReadable",
        "press_shop_v113_support_crane_fleet_identity_readable_runtime.png"),
}
if CANDIDATE not in MAPS:
    raise RuntimeError(f"Unknown LB_SUPPORT_CRANE_CANDIDATE={CANDIDATE!r}")
MAP = MAPS[CANDIDATE]
VIEWS = VIEWS_V113 if CANDIDATE in ("v113", "v116", "v117", "v118", "v119", "v120", "v121", "v122", "v123", "v124", "v125", "v126", "v127", "v128", "v129", "v130", "v131", "v132") else VIEWS_V112 if CANDIDATE == "v112" else VIEWS_V111 if CANDIDATE == "v111" else VIEWS_V110 if CANDIDATE == "v110" else VIEWS_V109 if CANDIDATE == "v109" else VIEWS_V038 if CANDIDATE == "v038" else VIEWS_V037 if CANDIDATE == "v037" else VIEWS_V036
if MODE not in VIEWS:
    raise RuntimeError(f"Unknown LB_SUPPORT_CRANE_CAPTURE={MODE!r}")
CAMERA_LABEL, FILENAME = VIEWS[MODE]
if CANDIDATE == "v116":
    FILENAME = FILENAME.replace("v113", "v116")
if CANDIDATE == "v117":
    FILENAME = FILENAME.replace("v113", "v117")
if CANDIDATE == "v118":
    FILENAME = FILENAME.replace("v113", "v118")
if CANDIDATE == "v119":
    FILENAME = FILENAME.replace("v113", "v119")
if CANDIDATE == "v120":
    FILENAME = FILENAME.replace("v113", "v120")
if CANDIDATE == "v121":
    FILENAME = FILENAME.replace("v113", "v121")
if CANDIDATE == "v122":
    FILENAME = FILENAME.replace("v113", "v122")
if CANDIDATE == "v123":
    FILENAME = FILENAME.replace("v113", "v123")
if CANDIDATE == "v124":
    FILENAME = FILENAME.replace("v113", "v124")
if CANDIDATE == "v125":
    FILENAME = FILENAME.replace("v113", "v125")
if CANDIDATE == "v126":
    FILENAME = FILENAME.replace("v113", "v126")
if CANDIDATE == "v127":
    FILENAME = FILENAME.replace("v113", "v127")
if CANDIDATE == "v128":
    FILENAME = FILENAME.replace("v113", "v128")
if CANDIDATE == "v129":
    FILENAME = FILENAME.replace("v113", "v129")
if CANDIDATE == "v130":
    FILENAME = FILENAME.replace("v113", "v130")
if CANDIDATE == "v131":
    FILENAME = FILENAME.replace("v113", "v131")
if CANDIDATE == "v132":
    FILENAME = FILENAME.replace("v113", "v132")
OUTPUT = (
    Path(unreal.Paths.project_saved_dir())
    / f"ValidationScreenshots/PressShopIntegration/{CANDIDATE}_pr004_support_crane_runtime"
    / FILENAME)
if DIAGNOSTIC_SUFFIX:
    OUTPUT = OUTPUT.with_name(f"{OUTPUT.stem}_{DIAGNOSTIC_SUFFIX}{OUTPUT.suffix}")
CAMERA_TAG = unreal.Name(f"LB.Capture.SupportCrane.{CANDIDATE}.{MODE}")
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
disabled_diagnostic_lights = []
if DIAGNOSTIC_LIGHT_LABELS:
    for diagnostic_actor in actors.get_all_level_actors():
        diagnostic_label = diagnostic_actor.get_actor_label()
        if diagnostic_label not in DIAGNOSTIC_LIGHT_LABELS:
            continue
        diagnostic_component = diagnostic_actor.get_component_by_class(unreal.SpotLightComponent)
        if diagnostic_component is None:
            raise RuntimeError(f"Diagnostic target is not a spotlight: {diagnostic_label}")
        diagnostic_component.set_editor_property("affects_world", False)
        diagnostic_component.set_editor_property("intensity", 0.0)
        disabled_diagnostic_lights.append(diagnostic_label)
    missing_diagnostic = sorted(set(DIAGNOSTIC_LIGHT_LABELS) - set(disabled_diagnostic_lights))
    if missing_diagnostic:
        raise RuntimeError(f"Missing diagnostic spotlight labels: {missing_diagnostic}")
    unreal.log(f"LINE_BOSS_SUPPORT_CRANE_DIAGNOSTIC_LIGHTS_OFF labels={disabled_diagnostic_lights}")
authored = next(
    (actor for actor in actors.get_all_level_actors()
     if actor.get_actor_label() == CAMERA_LABEL), None)
if authored is None:
    raise RuntimeError(f"Missing fixed camera {CAMERA_LABEL}")
capture_camera = actors.spawn_actor_from_class(
    unreal.CameraActor, authored.get_actor_location(), authored.get_actor_rotation())
capture_camera.set_actor_label(f"LB_PR004_V036_CAPTURE_{MODE.upper()}")
capture_camera.tags = [CAMERA_TAG]
capture_camera.camera_component.set_field_of_view(
    authored.camera_component.get_editor_property("field_of_view"))
capture_camera.camera_component.set_editor_property(
    "post_process_settings", authored.camera_component.get_editor_property("post_process_settings"))
capture_camera.camera_component.set_editor_property(
    "post_process_blend_weight", authored.camera_component.get_editor_property("post_process_blend_weight"))

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
if OUTPUT.exists():
    OUTPUT.unlink()

unreal.EditorLevelLibrary.editor_play_simulate()
started = time.monotonic()
handle = None
controller = None
capture_started_at = None


def fail(message):
    global handle
    unreal.log_error(f"LINE_BOSS_SUPPORT_CRANE_CAPTURE_FAIL mode={MODE} reason={message}")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.SystemLibrary.quit_editor()


def finish_tick(_delta_seconds):
    global handle
    if OUTPUT.exists() and OUTPUT.stat().st_size >= 1024:
        unreal.log(
            f"LINE_BOSS_SUPPORT_CRANE_CAPTURE_PASS mode={MODE} "
            f"phase={controller.get_phase()} output={OUTPUT}")
    elif time.monotonic() - capture_started_at < 80.0:
        return
    else:
        fail("screenshot_timeout")
        return
    unreal.unregister_slate_post_tick_callback(handle)
    handle = None
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.SystemLibrary.quit_editor()


def tick(_delta_seconds):
    global handle, controller, capture_started_at
    if time.monotonic() - started > 80.0:
        fail("runtime_phase_timeout")
        return
    world = unreal.EditorLevelLibrary.get_game_world()
    if world is None:
        return
    if controller is None:
        found = unreal.GameplayStatics.get_all_actors_of_class(
            world, unreal.LBSupportCraneController)
        if len(found) != 1:
            return
        controller = found[0]
        controller.set_editor_property("custom_time_dilation", 8.0)
        if not controller.discover_and_bind():
            fail("discover_and_bind=false")
            return
        if MODE in ("on_station", "hook_close"):
            steps = [
                controller.set_control_power(True),
                controller.set_safety_inputs(True, True, True, True),
                controller.set_primary_crane_clear(True),
                controller.dispatch_to_configured_service_point(),
            ]
            if not all(steps):
                fail(f"authority={steps}")
                return

    ready = controller.is_parked() if MODE in ("park", "fleet") else controller.is_at_service_point()
    if not ready or capture_started_at is not None:
        return
    cameras = unreal.GameplayStatics.get_all_actors_with_tag(world, CAMERA_TAG)
    if len(cameras) != 1:
        fail(f"fixed_camera_count={len(cameras)}")
        return

    capture_started_at = time.monotonic()
    controller.set_editor_property("custom_time_dilation", 0.001)
    unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
    unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
    unreal.SystemLibrary.execute_console_command(world, "r.HighResScreenshotDelay 8")
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    unreal.AutomationLibrary.finish_loading_before_screenshot()
    unreal.unregister_slate_post_tick_callback(handle)
    handle = None
    task = unreal.AutomationLibrary.take_high_res_screenshot(
        1920, 1080, str(OUTPUT), camera=cameras[0], force_game_view=True)
    if not task.is_valid_task():
        fail("invalid_screenshot_task")
        return
    handle = unreal.register_slate_post_tick_callback(finish_tick)


handle = unreal.register_slate_post_tick_callback(tick)
