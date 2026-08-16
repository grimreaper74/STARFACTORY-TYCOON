"""Fresh fixed-camera in-hall comparison of modular MR01-01 and aggregate MR01-02."""
import time
from pathlib import Path
import unreal

MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v270"
CAMERA = "LB_DOCK_V270_CAM_MR01_PAIR_COMPARISON"
OUT = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/SupportRobots/PressShopDockComparison_v270/press_shop_mr01_dock_pair_v270.png"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"failed to load {MAP}")
camera = next((actor for actor in actors.get_all_level_actors() if isinstance(actor, unreal.CameraActor) and actor.get_actor_label() == CAMERA), None)
if camera is None:
    raise RuntimeError(f"missing camera {CAMERA}")
OUT.parent.mkdir(parents=True, exist_ok=True)
world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.log(f"LINE_BOSS_PRESS_SHOP_MR01_DOCK_COMPARISON_V270_READY {OUT}")
# Request the latent task before the top-level ExecutePythonScript returns;
# its delay keeps the editor process alive while the loaded hall settles.
task = unreal.AutomationLibrary.take_high_res_screenshot(
    1920, 1080, str(OUT), camera=camera, delay=1.0, force_game_view=True
)
if not task.is_valid_task():
    raise RuntimeError("invalid screenshot task")
started = time.monotonic()
tick_handle = None

def finish_when_ready(_delta_seconds):
    global tick_handle
    if not task.is_task_done() and time.monotonic() - started < 60.0:
        return
    if not OUT.exists() or OUT.stat().st_size < 1024:
        unreal.log_error(f"LINE_BOSS_PRESS_SHOP_MR01_DOCK_COMPARISON_V270_FAIL {OUT}")
    else:
        unreal.log(f"LINE_BOSS_PRESS_SHOP_MR01_DOCK_COMPARISON_V270_PASS {OUT} {OUT.stat().st_size}")
    if tick_handle is not None:
        unreal.unregister_slate_post_tick_callback(tick_handle)
        tick_handle = None
    unreal.SystemLibrary.quit_editor()

tick_handle = unreal.register_slate_post_tick_callback(finish_when_ready)
