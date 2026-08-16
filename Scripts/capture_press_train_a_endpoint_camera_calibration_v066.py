"""Transiently calibrate elevated endpoint CCTV views on preserved v066 without saving the map."""

import os
import time
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressTrainADockCouplingEvidenceCandidate_v066"
CALIBRATIONS = {
    "s01_high": {
        "camera": "CA_MW_PTA_CAM_S01DieSideFlow_v066",
        "location": unreal.Vector(850.0, -720.0, 650.0),
        "target": unreal.Vector(0.0, -120.0, 105.0),
        "file": "press_train_a_v066_s01_high_calibration.png",
    },
    "s07_high": {
        "camera": "CA_MW_PTA_CAM_S07DieSideFlow_v066",
        "location": unreal.Vector(900.0, 5450.0, 700.0),
        "target": unreal.Vector(0.0, 4850.0, 120.0),
        "file": "press_train_a_v066_s07_high_calibration.png",
    },
}

capture_id = os.environ.get("LB_PRESS_TRAIN_A_ENDPOINT_CALIBRATION", "s01_high").lower()
if capture_id not in CALIBRATIONS:
    raise RuntimeError(f"unknown endpoint calibration: {capture_id}")
calibration = CALIBRATIONS[capture_id]
output = (Path(unreal.Paths.project_saved_dir()) /
          "ValidationScreenshots/PressShopIntegration/press_train_a_v066_calibration" /
          calibration["file"])
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
camera = next((actor for actor in actors_api.get_all_level_actors()
               if actor.get_actor_label() == calibration["camera"]), None)
if camera is None:
    raise RuntimeError(calibration["camera"])
camera.set_actor_location(calibration["location"], False, False)
camera.set_actor_rotation(
    unreal.MathLibrary.find_look_at_rotation(calibration["location"], calibration["target"]), False)
settings = camera.camera_component.get_editor_property("post_process_settings")
settings.set_editor_properties({
    "override_auto_exposure_method": True,
    "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
    "override_auto_exposure_min_brightness": True,
    "override_auto_exposure_max_brightness": True,
    "auto_exposure_min_brightness": 1.0,
    "auto_exposure_max_brightness": 1.0,
    "override_auto_exposure_bias": True,
    "auto_exposure_bias": 1.0,
})
camera.camera_component.set_editor_property("post_process_settings", settings)
camera.camera_component.set_editor_property("post_process_blend_weight", 1.0)
camera.camera_component.set_editor_property("field_of_view", 58.0)
output.parent.mkdir(parents=True, exist_ok=True)
if output.exists():
    output.unlink()
world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
unreal.SystemLibrary.execute_console_command(world, "r.HighResScreenshotDelay 28")
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()
task = unreal.AutomationLibrary.take_high_res_screenshot(
    1920, 1080, str(output), camera=camera, mask_enabled=False, capture_hdr=False,
    comparison_tolerance=unreal.ComparisonTolerance.LOW,
    comparison_notes=f"Train A v066 transient endpoint calibration: {capture_id}",
    delay=0.0, force_game_view=True,
)
if not task.is_valid_task():
    raise RuntimeError(f"invalid screenshot task: {capture_id}")
started = time.monotonic()
handle = None


def finish(_delta):
    global handle
    elapsed = time.monotonic() - started
    if elapsed >= 3.0 and output.exists() and output.stat().st_size >= 1024:
        unreal.log(f"PRESS_TRAIN_A_ENDPOINT_CALIBRATION_PASS id={capture_id} path={output}")
    elif elapsed < 55.0:
        return
    else:
        unreal.log_error(f"PRESS_TRAIN_A_ENDPOINT_CALIBRATION_FAIL id={capture_id} path={output}")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.SystemLibrary.quit_editor()


handle = unreal.register_slate_post_tick_callback(finish)
