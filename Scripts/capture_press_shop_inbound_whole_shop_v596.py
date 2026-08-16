"""Single-shot whole-shop evidence capture for v596."""
from pathlib import Path
import time
import unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP = "/Game/LineBoss/Developer/Validation/LB_PressShop_InboundReleaseCandidate_v596"
LABEL = "LB_CAM_InboundRelease_WholeShop_v596"
PATH = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/PressShopIntegration/inbound_release_v596/whole_press_shop_context.png"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP): raise RuntimeError(MAP)
PATH.parent.mkdir(parents=True, exist_ok=True)
camera = next((a for a in actors.get_all_level_actors() if a.get_actor_label() == LABEL), None)
if camera is None: raise RuntimeError(LABEL)
world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()
task = unreal.AutomationLibrary.take_high_res_screenshot(1920,1080,str(PATH),camera=camera,mask_enabled=False,capture_hdr=False,delay=0,force_game_view=True)
started=time.monotonic(); handle=None
def tick(_dt):
    global handle
    elapsed=time.monotonic()-started
    if elapsed < 1.0 or (not task.is_task_done() and elapsed < 45.0): return
    if not PATH.exists() or PATH.stat().st_size <= 1024:
        unreal.log_error(f"LINE_BOSS_INBOUND_V596_WHOLE_CAPTURE_FAIL {PATH}")
    else:
        unreal.log(f"LINE_BOSS_INBOUND_V596_WHOLE_CAPTURE_PASS {PATH}")
    unreal.unregister_slate_post_tick_callback(handle); handle=None; unreal.SystemLibrary.quit_editor()
handle=unreal.register_slate_post_tick_callback(tick)
