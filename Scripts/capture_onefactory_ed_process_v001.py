"""Capture the visible six-tank ED process in the current OneFactory map.

This is a read-only presentation capture.  It uses SceneCapture2D rather than
the editor screenshot queue, because -ExecutePythonScript ends its own editor
session before a queued Slate screenshot can reliably complete.  Nothing is
saved to the level.
"""

from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Factory/OneFactory/v001/Maps/LB_MoorcrossWorks_OneFactory_v001"
OUTPUT = Path(unreal.Paths.project_saved_dir()) / (
    "ValidationScreenshots/OneFactory/Current_EDCoat_TrackedSixTank_v004.png"
)
BASE_COLOUR_OUTPUT = Path(unreal.Paths.project_saved_dir()) / (
    "ValidationScreenshots/OneFactory/Current_EDCoat_TrackedSixTank_v004_basecolour.png"
)

if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load OneFactory map")

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
camera_location = unreal.Vector(6500.0, -2350.0, 2100.0)
ed_focus = unreal.Vector(6500.0, -5300.0, 120.0)
camera_rotation = unreal.MathLibrary.find_look_at_rotation(
    camera_location, ed_focus)
camera = unreal.EditorLevelLibrary.spawn_actor_from_class(
    unreal.CameraActor, camera_location, camera_rotation,
)
if camera is None:
    raise RuntimeError("Could not create temporary ED capture camera")
camera.set_actor_label("TEMP_EDCoatCaptureCamera")
camera_component = camera.get_component_by_class(unreal.CameraComponent)
if camera_component is None:
    unreal.EditorLevelLibrary.destroy_actor(camera)
    raise RuntimeError("Temporary ED capture camera has no camera component")
camera_component.set_editor_property("field_of_view", 64.0)

world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
unreal.SystemLibrary.execute_console_command(world, "r.ForceDebugViewModes 0")
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()

target = unreal.RenderingLibrary.create_render_target2d(
    world, 1920, 1080, unreal.TextureRenderTargetFormat.RTF_RGBA8,
    unreal.LinearColor(0.015, 0.015, 0.015, 1.0), False, False,
)
target.set_editor_property("target_gamma", 2.2)
capture = unreal.EditorLevelLibrary.spawn_actor_from_class(
    unreal.SceneCapture2D, camera.get_actor_location(), camera.get_actor_rotation(),
)
if capture is None:
    unreal.EditorLevelLibrary.destroy_actor(camera)
    raise RuntimeError("Could not create temporary ED scene capture")
capture.set_actor_label("TEMP_EDCoatSceneCapture")
capture.set_actor_location(camera.get_actor_location(), False, False)
capture.set_actor_rotation(camera.get_actor_rotation(), False)
component = capture.get_editor_property("capture_component2d")
component.set_editor_properties({
    "texture_target": target,
    "capture_source": unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR,
    "capture_every_frame": False,
    "capture_on_movement": False,
    "fov_angle": camera_component.get_editor_property("field_of_view"),
})
post = component.get_editor_property("post_process_settings")
post.set_editor_properties({
    "override_auto_exposure_method": True,
    "auto_exposure_method": unreal.AutoExposureMethod.AEM_MANUAL,
    "override_auto_exposure_bias": True,
    "auto_exposure_bias": 0.0,
})
component.set_editor_property("post_process_settings", post)
component.set_editor_property("post_process_blend_weight", 1.0)
component.capture_scene()
unreal.RenderingLibrary.export_render_target(
    world, target, str(OUTPUT.parent), OUTPUT.name,
)
component.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_BASE_COLOR)
component.set_editor_property("post_process_blend_weight", 0.0)
component.capture_scene()
unreal.RenderingLibrary.export_render_target(
    world, target, str(BASE_COLOUR_OUTPUT.parent), BASE_COLOUR_OUTPUT.name,
)
unreal.EditorLevelLibrary.destroy_actor(capture)
unreal.EditorLevelLibrary.destroy_actor(camera)
if (not OUTPUT.exists() or OUTPUT.stat().st_size < 1024
        or not BASE_COLOUR_OUTPUT.exists() or BASE_COLOUR_OUTPUT.stat().st_size < 1024):
    raise RuntimeError(f"ED process scene capture did not write: {OUTPUT}")
unreal.log(
    f"LINE_BOSS_ED_PROCESS_CAPTURE_PASS path={OUTPUT} bytes={OUTPUT.stat().st_size}"
)
