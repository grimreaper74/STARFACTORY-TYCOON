"""Offscreen FinalColor capture of the existing disposable PR005 HMI QA level.

Avoids the commandlet viewport HighResShot buffer, which has produced a
black/white placeholder PNG.  This script does not save or alter the level.
"""

from pathlib import Path

import unreal


MAP_PATH = "/Game/LineBoss/Developer/Validation/LB_PR005_DetailedHMI_v001"
CAMERA_LABEL = "PR005_HMI_QA_Camera"
OUT_DIR = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/PR005/HMI/Candidate_v001"
OUT_NAME = "pr005_detailed_hmi_texture_v003_scenecapture.png"


levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP_PATH):
    raise RuntimeError(f"Could not load {MAP_PATH}")
camera = next((a for a in actors.get_all_level_actors()
               if a.get_actor_label() == CAMERA_LABEL), None)
if camera is None:
    raise RuntimeError(f"Missing fixed QA camera {CAMERA_LABEL}")

out = OUT_DIR / OUT_NAME
if out.exists():
    raise RuntimeError(f"Refusing to overwrite evidence: {out}")
OUT_DIR.mkdir(parents=True, exist_ok=True)
world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()

target = unreal.RenderingLibrary.create_render_target2d(
    world,
    1920,
    1080,
    unreal.TextureRenderTargetFormat.RTF_RGBA8,
    unreal.LinearColor(0.015, 0.015, 0.015, 1.0),
    False,
    False,
)
target.set_editor_property("target_gamma", 2.2)
capture = actors.spawn_actor_from_class(
    unreal.SceneCapture2D,
    camera.get_actor_location(),
    camera.get_actor_rotation(),
)
capture.set_actor_label("LB_PR005_HMI_QA_SCENECAPTURE_TEMP_NOT_SAVED")
component = capture.get_editor_property("capture_component2d")
component.set_editor_properties({
    "texture_target": target,
    "capture_source": unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR,
    "capture_every_frame": False,
    "capture_on_movement": False,
    "fov_angle": camera.get_editor_property("camera_component").get_editor_property("field_of_view"),
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
unreal.RenderingLibrary.export_render_target(world, target, str(OUT_DIR), OUT_NAME)
actors.destroy_actor(capture)
unreal.log(f"LINE_BOSS_PR005_HMI_QA_SCENECAPTURE_V003_PASS output={out}")
