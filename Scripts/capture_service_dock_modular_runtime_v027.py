"""Capture the corrected isolated modular dock family."""
import time
from pathlib import Path
import unreal

VERSION = 29
MAP = f"/Game/LineBoss/Developer/Validation/LB_ServiceDockModularRuntime_v{VERSION:03d}"
CAMERA = f"LB_DOCK_V{VERSION:03d}_CAM_FAMILY"
OUT = Path(unreal.Paths.project_saved_dir()) / f"ValidationScreenshots/SupportRobots/ServiceDocks/ModularRuntime_v{VERSION:03d}/service_dock_modular_runtime_v{VERSION:03d}_family_runtime_override_v030.png"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"failed to load {MAP}")
camera = next((actor for actor in actors.get_all_level_actors() if isinstance(actor, unreal.CameraActor) and actor.get_actor_label() == CAMERA), None)
if camera is None:
    raise RuntimeError(f"fixed camera missing: {CAMERA}")
OUT.parent.mkdir(parents=True, exist_ok=True)
world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()
task = unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, str(OUT), camera=camera, force_game_view=True)
if not task.is_valid_task():
    raise RuntimeError("invalid screenshot task")
started = time.monotonic()
tick_handle = None

def finish_when_ready(_delta_seconds):
    global tick_handle
    if not task.is_task_done() and time.monotonic() - started < 60.0:
        return
    if not OUT.exists() or OUT.stat().st_size < 1024:
        unreal.log_error(f"LINE_BOSS_SERVICE_DOCK_V027_CAPTURE_FAIL {OUT}")
    else:
        unreal.log(f"LINE_BOSS_SERVICE_DOCK_V027_CAPTURE_PASS {OUT} {OUT.stat().st_size}")
    if tick_handle is not None:
        unreal.unregister_slate_post_tick_callback(tick_handle)
        tick_handle = None
    unreal.SystemLibrary.quit_editor()

tick_handle = unreal.register_slate_post_tick_callback(finish_when_ready)
