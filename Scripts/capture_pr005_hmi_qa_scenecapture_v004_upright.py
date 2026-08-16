"""Capture the existing disposable PR005 HMI QA level upright; no source/runtime/v913 edits."""
from pathlib import Path
import unreal

MAP = "/Game/LineBoss/Developer/Validation/LB_PR005_DetailedHMI_v001"
HMI_LABEL = "PR005_DetailedHMI_Meshy_v001_TexturePreservation"
CAMERA_LABEL = "PR005_HMI_QA_Camera"
OUT_DIR = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/PR005/HMI/Candidate_v001"
OUT_NAME = "pr005_detailed_hmi_texture_v004_upright.png"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
hmi = next((a for a in actors.get_all_level_actors() if a.get_actor_label() == HMI_LABEL), None)
if hmi is None:
    raise RuntimeError("Missing QA HMI actor")
hmi.set_actor_rotation(unreal.Rotator(roll=0.0, pitch=0.0, yaw=180.0), False)
hmi.static_mesh_component.set_visibility(True, True)
origin, extent = hmi.get_actor_bounds(False)
if origin.z - extent.z < -0.5:
    raise RuntimeError(f"HMI remains below QA floor: origin={origin} extent={extent}")
camera = next((a for a in actors.get_all_level_actors() if a.get_actor_label() == CAMERA_LABEL), None)
if camera is None:
    raise RuntimeError("Missing QA camera")
target_pt = unreal.Vector(0.0, 0.0, 64.0)
camera.set_actor_location(unreal.Vector(185.0, 285.0, 155.0), False, False)
camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(), target_pt), False)
OUT_DIR.mkdir(parents=True, exist_ok=True)
out = OUT_DIR / OUT_NAME
if out.exists():
    raise RuntimeError(f"Refusing to overwrite evidence: {out}")
world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()
rt = unreal.RenderingLibrary.create_render_target2d(world, 1920, 1080, unreal.TextureRenderTargetFormat.RTF_RGBA8, unreal.LinearColor(0.015,0.015,0.015,1.0), False, False)
rt.set_editor_property("target_gamma", 2.2)
# Retain a Python reference until export completes; otherwise commandlet GC releases the render target.
keep_alive = rt
capture = actors.spawn_actor_from_class(unreal.SceneCapture2D, camera.get_actor_location(), camera.get_actor_rotation())
capture.set_actor_label("LB_PR005_HMI_QA_SCENECAPTURE_TEMP_NOT_SAVED")
comp = capture.get_editor_property("capture_component2d")
comp.set_editor_properties({"texture_target":rt,"capture_source":unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR,"capture_every_frame":False,"capture_on_movement":False,"fov_angle":36.0})
post = comp.get_editor_property("post_process_settings")
post.set_editor_properties({"override_auto_exposure_method":True,"auto_exposure_method":unreal.AutoExposureMethod.AEM_MANUAL,"override_auto_exposure_bias":True,"auto_exposure_bias":0.0})
comp.set_editor_property("post_process_settings",post)
comp.set_editor_property("post_process_blend_weight",1.0)
comp.capture_scene()
component_ref = comp
component_ref.capture_scene()
unreal.RenderingLibrary.export_render_target(world,keep_alive,str(OUT_DIR),OUT_NAME)
actors.destroy_actor(capture)
unreal.log(f"LINE_BOSS_PR005_HMI_QA_SCENECAPTURE_V004_UPRIGHT_PASS output={out} bounds_origin={origin} bounds_extent={extent}")


