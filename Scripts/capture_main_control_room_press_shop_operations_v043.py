"""Capture one v043 operations view per clean normal Unreal process."""

import os
import time
from pathlib import Path

import unreal

MAP = "/Game/LineBoss/Maps/LB_MainControlRoom_PressShopOperationsEvidenceCandidate_v043"
CAPTURES = {
    "standing": ("LB_MCR_V043_CAM_StandingOperations", "main_control_room_v043_standing_operations.png"),
    "screen": ("LB_MCR_V043_CAM_OperationsScreenClose", "main_control_room_v043_operations_screen_close.png"),
}
capture_id = os.environ.get("LB_MCR_V043_CAPTURE", "standing").lower()
if capture_id not in CAPTURES:
    raise RuntimeError(capture_id)
camera_label, filename = CAPTURES[capture_id]
output = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/ControlRoom/v043_press_shop_operations" / filename
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
camera = next((actor for actor in actors.get_all_level_actors() if actor.get_actor_label() == camera_label), None)
if camera is None:
    raise RuntimeError(camera_label)
operations = next((actor for actor in actors.get_all_level_actors()
                   if actor.get_class().get_name() == "LBControlRoomOperationsConsole"), None)
if operations is None:
    raise RuntimeError("operations console missing")
operations.refresh_for_editor_evidence()
output.parent.mkdir(parents=True, exist_ok=True)
if output.exists(): output.unlink()
world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
unreal.SystemLibrary.execute_console_command(world, "r.HighResScreenshotDelay 28")
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()
task = unreal.AutomationLibrary.take_high_res_screenshot(
    1920, 1080, str(output), camera=camera, mask_enabled=False, capture_hdr=False,
    comparison_tolerance=unreal.ComparisonTolerance.LOW,
    comparison_notes=f"Cairnwell Moorcross v043 Press Shop operations {capture_id}",
    delay=0.0, force_game_view=True)
if not task.is_valid_task():
    raise RuntimeError(f"invalid screenshot task for {capture_id}")
started = time.monotonic()
handle = None

def finish(_delta):
    global handle
    elapsed = time.monotonic() - started
    if elapsed >= 3.0 and output.exists() and output.stat().st_size >= 1024:
        unreal.log(f"LB_MCR_V043_CAPTURE_PASS id={capture_id} path={output}")
    elif elapsed < 55.0:
        return
    else:
        unreal.log_error(f"LB_MCR_V043_CAPTURE_FAIL id={capture_id} path={output}")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.SystemLibrary.quit_editor()

handle = unreal.register_slate_post_tick_callback(finish)
