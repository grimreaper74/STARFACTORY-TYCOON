"""Capture the isolated modular dock family with its fixed authored camera."""
import time
from pathlib import Path
import unreal

MAP = "/Game/LineBoss/Developer/Validation/LB_ServiceDockModularRuntime_v026"
OUT = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/SupportRobots/ServiceDocks/ModularRuntime_v026/service_dock_modular_runtime_v026_family.png"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"failed to load {MAP}")
camera = next((actor for actor in actors.get_all_level_actors() if isinstance(actor, unreal.CameraActor) and actor.get_actor_label() == "LB_DOCK_V026_CAM_FAMILY"), None)
if camera is None:
    raise RuntimeError("fixed family camera missing")
OUT.parent.mkdir(parents=True, exist_ok=True)
world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
unreal.SystemLibrary.execute_console_command(world, "r.HighResScreenshotDelay 20")
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()
task = unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, str(OUT), camera=camera, force_game_view=True)
deadline = time.monotonic() + 90
while not OUT.exists() and time.monotonic() < deadline:
    time.sleep(0.25)
if not OUT.exists():
    raise RuntimeError("screenshot did not complete")
unreal.log(f"LINE_BOSS_SERVICE_DOCK_MODULAR_RUNTIME_CAPTURE_V026_PASS {OUT}")
