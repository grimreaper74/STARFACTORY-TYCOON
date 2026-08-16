"""Capture PR-004 final and base-colour buffers from one fixed camera."""

from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Developer/Validation/PR004/LB_PR004_Depackaging_Candidate_v002"
CAMERA = "LB_PR004_CAM_Overview_NE"
OUT = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/PR004/Candidate_v002/Diagnostic"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
camera = next((actor for actor in actors.get_all_level_actors() if actor.get_actor_label() == CAMERA), None)
if camera is None:
    raise RuntimeError(f"Missing {CAMERA}")

world = unreal.EditorLevelLibrary.get_editor_world()
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
target = unreal.RenderingLibrary.create_render_target2d(
    world, 1920, 1080, unreal.TextureRenderTargetFormat.RTF_RGBA8,
    unreal.LinearColor(0.018, 0.022, 0.026, 1.0), False, False,
)
target.set_editor_property("target_gamma", 2.2)
capture = actors.spawn_actor_from_class(unreal.SceneCapture2D, camera.get_actor_location(), camera.get_actor_rotation())
capture.set_actor_label("LB_PR004_RenderDiagnostic_TEMP")
component = capture.get_editor_property("capture_component2d")
camera_component = camera.get_editor_property("camera_component")
component.set_editor_properties({
    "texture_target": target,
    "capture_source": unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR,
    "capture_every_frame": False,
    "capture_on_movement": False,
    "fov_angle": camera_component.get_editor_property("field_of_view"),
    "post_process_blend_weight": 0.0,
})

OUT.mkdir(parents=True, exist_ok=True)
component.capture_scene()
unreal.RenderingLibrary.export_render_target(world, target, str(OUT), "pr004_overview_ne_finalcolor_diagnostic.png")
component.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_BASE_COLOR)
component.capture_scene()
unreal.RenderingLibrary.export_render_target(world, target, str(OUT), "pr004_overview_ne_basecolor_diagnostic.png")
actors.destroy_actor(capture)
unreal.log(f"LINE_BOSS_PR004_RENDER_DIAGNOSTIC={OUT}")
