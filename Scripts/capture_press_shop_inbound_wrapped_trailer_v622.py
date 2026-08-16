"""Capture fixed-camera visual review images from the exact v616 validation map."""
from pathlib import Path
import time
import unreal


MAP = "/Game/LineBoss/Developer/Validation/LB_PressShop_InboundWrappedTrailerCandidate_v616"
OUTPUT = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/PressShopIntegration/inbound_wrapped_trailer_v622"
CAPTURES = [
    ("LB_CAM_InboundRelease_Process_v597", "01_process_context.png"),
    ("LB_CAM_InboundRelease_Handoff_v597", "02_handoff_context.png"),
    ("LB_CAM_InboundRelease_WholeShop_v597", "03_whole_shop_context.png"),
]

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)

OUTPUT.mkdir(parents=True, exist_ok=True)
world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()

index = 0
task = None
started = time.monotonic()
handle = None


def begin_capture():
    global task, started
    label, filename = CAPTURES[index]
    camera = next((a for a in actors.get_all_level_actors() if a.get_actor_label() == label), None)
    if camera is None:
        raise RuntimeError(label)
    path = OUTPUT / filename
    task = unreal.AutomationLibrary.take_high_res_screenshot(
        1920,
        1080,
        str(path),
        camera=camera,
        mask_enabled=False,
        capture_hdr=False,
        delay=8,
        force_game_view=True,
    )
    started = time.monotonic()


def tick(_dt):
    global index, handle
    elapsed = time.monotonic() - started
    if elapsed < 9.0 or (not task.is_task_done() and elapsed < 60.0):
        return
    path = OUTPUT / CAPTURES[index][1]
    if not path.exists() or path.stat().st_size <= 1024:
        unreal.log_error(f"LINE_BOSS_INBOUND_V622_CAPTURE_FAIL {path}")
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
        unreal.SystemLibrary.quit_editor()
        return
    unreal.log(f"LINE_BOSS_INBOUND_V622_CAPTURE_PASS {path}")
    index += 1
    if index >= len(CAPTURES):
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
        unreal.SystemLibrary.quit_editor()
        return
    begin_capture()


begin_capture()
handle = unreal.register_slate_post_tick_callback(tick)
