from pathlib import Path
import time
import unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP = "/Game/LineBoss/Developer/Validation/LB_InboundCoilDeliveryReview_v507"
OUT = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/PressShopIntegration/inbound_coil_delivery_v507/inbound_overview.png"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError("Could not load v507")
camera = next((a for a in actors.get_all_level_actors() if a.get_actor_label() == "LB_CAM_InboundCoilDelivery_Review_v507"), None)
if camera is None:
    raise RuntimeError("Missing v507 camera")
OUT.parent.mkdir(parents=True, exist_ok=True)
world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()
task = unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, str(OUT), camera=camera, mask_enabled=False, capture_hdr=False, delay=0, force_game_view=True)
if not task.is_valid_task():
    raise RuntimeError("Invalid screenshot task")
started = time.monotonic()
handle = None
def done(_dt):
    global handle
    if not task.is_task_done() and time.monotonic() - started < 45:
        return
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    passed = OUT.exists() and OUT.stat().st_size > 1024
    unreal.log(("LINE_BOSS_INBOUND_REVIEW_V507_CAPTURE_PASS " if passed else "LINE_BOSS_INBOUND_REVIEW_V507_CAPTURE_FAIL ") + str(OUT))
    unreal.SystemLibrary.quit_editor()
handle = unreal.register_slate_post_tick_callback(done)
