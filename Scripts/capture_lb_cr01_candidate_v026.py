"""Capture fresh fixed-camera Unreal evidence for LB-CR01 candidate v026."""

import os
import time
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Developer/Validation/LB_CR01_CleaningAMR_Candidate_v026"
CAPTURES = {
    "oblique": ("LB_CR01_V026_CAM_Oblique", "lb_cr01_v026_oblique_lights.png"),
    "side": ("LB_CR01_V026_CAM_Side", "lb_cr01_v026_side_lights.png"),
    "top": ("LB_CR01_V026_CAM_Top", "lb_cr01_v026_top_lights.png"),
}
capture_id = os.environ.get("LB_CR01_CAPTURE", "oblique").lower()
if capture_id not in CAPTURES:
    raise RuntimeError(f"Unknown LB_CR01_CAPTURE {capture_id!r}")
camera_label, filename = CAPTURES[capture_id]
output = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/LB_CR01/Candidate_v026" / filename

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels.load_level(MAP)
camera = next((actor for actor in actors.get_all_level_actors() if actor.get_actor_label() == camera_label), None)
if camera is None:
    raise RuntimeError(f"Missing fixed camera {camera_label}")

output.parent.mkdir(parents=True, exist_ok=True)
if output.exists():
    output.unlink()
world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
unreal.SystemLibrary.execute_console_command(world, "r.HighResScreenshotDelay 24")
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()
task = unreal.AutomationLibrary.take_high_res_screenshot(
    1600, 1000, str(output), camera=camera, mask_enabled=False, capture_hdr=False,
    comparison_tolerance=unreal.ComparisonTolerance.LOW,
    comparison_notes=f"LB-CR01 Candidate v026 {capture_id} lights/material/runtime candidate",
    delay=0.0, force_game_view=True,
)
if not task.is_valid_task():
    raise RuntimeError("Invalid screenshot task")

started = time.monotonic()
tick_handle = None


def finish(_delta):
    global tick_handle
    elapsed = time.monotonic() - started
    if elapsed >= 3.0 and output.exists() and output.stat().st_size >= 1024:
        unreal.log(f"LINE_BOSS_LB_CR01_V026_CAPTURE_PASS id={capture_id} path={output}")
    elif elapsed < 55.0:
        return
    else:
        unreal.log_error(f"LINE_BOSS_LB_CR01_V026_CAPTURE_FAIL id={capture_id}")
    if tick_handle is not None:
        unreal.unregister_slate_post_tick_callback(tick_handle)
        tick_handle = None
    unreal.SystemLibrary.quit_editor()


tick_handle = unreal.register_slate_post_tick_callback(finish)
