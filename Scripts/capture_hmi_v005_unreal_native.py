"""Capture the Unreal-native HMI v005 comparison candidate."""

from pathlib import Path
import unreal

MAP = "/Game/LineBoss/Developer/Validation/LB_HMI05_UnrealNativeValidation"
CAMERA = "LB_CAM_HMI05_Front"
OUT = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/HMI"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels.load_level(MAP)
camera = next((a for a in actors.get_all_level_actors() if a.get_actor_label() == CAMERA), None)
if camera is None:
    raise RuntimeError(f"Missing {CAMERA}")
world = unreal.EditorLevelLibrary.get_editor_world()
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
target = unreal.RenderingLibrary.create_render_target2d(
    world, 1920, 1080, unreal.TextureRenderTargetFormat.RTF_RGBA8,
    unreal.LinearColor(0.03, 0.03, 0.03, 1.0), False, False,
)
target.set_editor_property("target_gamma", 2.2)
capture = actors.spawn_actor_from_class(unreal.SceneCapture2D, camera.get_actor_location(), camera.get_actor_rotation())
capture.set_actor_label("LB_HMI05_Capture_TEMP")
component = capture.get_editor_property("capture_component2d")
component.set_editor_properties({
    "texture_target": target,
    "capture_source": unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR,
    "capture_every_frame": False,
    "capture_on_movement": False,
    "fov_angle": camera.get_editor_property("camera_component").get_editor_property("field_of_view"),
    "post_process_blend_weight": 0.0,
})
OUT.mkdir(parents=True, exist_ok=True)
component.capture_scene()
unreal.RenderingLibrary.export_render_target(world, target, str(OUT), "shared_hmi_v005_unreal_native_final.png")
component.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_BASE_COLOR)
component.capture_scene()
unreal.RenderingLibrary.export_render_target(world, target, str(OUT), "shared_hmi_v005_unreal_native_basecolor.png")
actors.destroy_actor(capture)
unreal.log(f"LINE_BOSS_HMI05_NATIVE_CAPTURE_PASS dir={OUT}")
