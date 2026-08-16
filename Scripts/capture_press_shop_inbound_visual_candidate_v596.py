"""Capture fixed-camera visual evidence for inbound release candidate v596."""
from pathlib import Path
import time
import unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP = "/Game/LineBoss/Developer/Validation/LB_PressShop_InboundReleaseCandidate_v596"
OUT = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/PressShopIntegration/inbound_release_v596"
SHOTS = [
    ("LB_CAM_InboundRelease_Process_v596", "inbound_process_context.png"),
    ("LB_CAM_InboundRelease_Handoff_v596", "inbound_handoff_to_pr003.png"),
    ("LB_CAM_InboundRelease_WholeShop_v596", "whole_press_shop_context.png"),
]
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
OUT.mkdir(parents=True, exist_ok=True)
world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()

index = 0
task = None
started = 0.0
handle = None

def begin():
    global task, started
    label, filename = SHOTS[index]
    camera = next((a for a in actors.get_all_level_actors() if a.get_actor_label() == label), None)
    if camera is None:
        raise RuntimeError(f"Missing fixed camera {label}")
    task = unreal.AutomationLibrary.take_high_res_screenshot(
        1920, 1080, str(OUT / filename), camera=camera, mask_enabled=False,
        capture_hdr=False, delay=0, force_game_view=True)
    if not task.is_valid_task():
        raise RuntimeError(f"Invalid screenshot task for {label}")
    started = time.monotonic()

def tick(_dt):
    global index, handle
    elapsed = time.monotonic() - started
    # The automation task can report done one Slate tick before the PNG has
    # finished committing.  Give each capture a short settling interval.
    if elapsed < 1.0:
        return
    if not task.is_task_done() and elapsed < 45.0:
        return
    label, filename = SHOTS[index]
    path = OUT / filename
    if not path.exists() or path.stat().st_size <= 1024:
        unreal.log_error(f"LINE_BOSS_INBOUND_V596_CAPTURE_FAIL {label} {path}")
        unreal.SystemLibrary.quit_editor()
        return
    unreal.log(f"LINE_BOSS_INBOUND_V596_CAPTURE_PASS {label} {path}")
    index += 1
    if index < len(SHOTS):
        begin()
        return
    unreal.unregister_slate_post_tick_callback(handle)
    handle = None
    unreal.SystemLibrary.quit_editor()

begin()
handle = unreal.register_slate_post_tick_callback(tick)
