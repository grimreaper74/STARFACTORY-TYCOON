"""Deterministic FinalColorLDR scene-capture evidence for HMI v004."""

from pathlib import Path
import unreal

MAP = "/Game/LineBoss/Developer/Validation/LB_HMI04_ModelingValidation"
CAMERA = "LB_CAM_HMI04_Front"
OUT_DIR = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/HMI"
OUT_NAME = "shared_hmi_v004_unreal_modeling_final.png"
BASE_NAME = "shared_hmi_v004_unreal_modeling_basecolor.png"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels.load_level(MAP)
camera = next((a for a in actors.get_all_level_actors() if a.get_actor_label() == CAMERA), None)
if camera is None:
    raise RuntimeError(f"Missing camera {CAMERA}")

world = unreal.EditorLevelLibrary.get_editor_world()
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
target = unreal.RenderingLibrary.create_render_target2d(
    world, 1920, 1080, unreal.TextureRenderTargetFormat.RTF_RGBA8,
    unreal.LinearColor(0.005, 0.005, 0.005, 1.0), False, False,
)
target.set_editor_property("target_gamma", 2.2)

capture = actors.spawn_actor_from_class(
    unreal.SceneCapture2D, camera.get_actor_location(), camera.get_actor_rotation()
)
capture.set_actor_label("LB_HMI04_FinalColorCapture_TEMP")
component = capture.get_editor_property("capture_component2d")
component.set_editor_properties({
    "texture_target": target,
    "capture_source": unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR,
    "capture_every_frame": False,
    "capture_on_movement": False,
    "fov_angle": camera.get_editor_property("camera_component").get_editor_property("field_of_view"),
})
# Lock exposure on the capture itself.  A black test-stage background makes
# automatic exposure lift the cabinet into white clipping.
capture_pp = component.get_editor_property("post_process_settings")
capture_pp.set_editor_properties({
    "override_auto_exposure_method": True,
    "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
    "override_auto_exposure_min_brightness": True,
    "override_auto_exposure_max_brightness": True,
    "auto_exposure_min_brightness": 0.03,
    "auto_exposure_max_brightness": 0.03,
    "override_auto_exposure_bias": True,
    "auto_exposure_bias": 0.0,
})
component.set_editor_property("post_process_settings", capture_pp)
component.set_editor_property("post_process_blend_weight", 1.0)
component.capture_scene()

OUT_DIR.mkdir(parents=True, exist_ok=True)
unreal.RenderingLibrary.export_render_target(world, target, str(OUT_DIR), OUT_NAME)
component.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_BASE_COLOR)
component.set_editor_property("post_process_blend_weight", 0.0)
component.capture_scene()
unreal.RenderingLibrary.export_render_target(world, target, str(OUT_DIR), BASE_NAME)
actors.destroy_actor(capture)
unreal.log(f"LINE_BOSS_HMI04_FINAL_CAPTURE path={OUT_DIR / OUT_NAME}")
