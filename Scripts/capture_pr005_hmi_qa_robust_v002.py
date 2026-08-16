"""Robust, non-destructive screenshot capture for the disposable PR005 HMI QA map.

This deliberately does not create, modify, or save a map.  It only opens the
existing QA level, gives the editor renderer time to settle, requests a
fixed-camera high-res capture, and keeps the Python host alive until a real
PNG is written.
"""

from __future__ import annotations

import time
from pathlib import Path

import unreal


MAP_PATH = "/Game/LineBoss/Developer/Validation/LB_PR005_DetailedHMI_v001"
CAMERA_LABEL = "PR005_HMI_QA_Camera"
OUT = Path(unreal.Paths.project_saved_dir()) / (
    "ValidationScreenshots/PR005/HMI/Candidate_v001/"
    "pr005_detailed_hmi_texture_v002_robust.png"
)


unreal.EditorPythonScripting.set_keep_python_script_alive(True)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP_PATH):
    raise RuntimeError(f"Could not load {MAP_PATH}")

camera = next(
    (actor for actor in actors.get_all_level_actors()
     if actor.get_actor_label() == CAMERA_LABEL),
    None,
)
if camera is None:
    raise RuntimeError(f"Missing fixed QA camera {CAMERA_LABEL}")
if OUT.exists():
    raise RuntimeError(f"Refusing to overwrite evidence: {OUT}")
OUT.parent.mkdir(parents=True, exist_ok=True)

world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
unreal.SystemLibrary.execute_console_command(world, "r.ForceDebugViewModes 0")
unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
unreal.SystemLibrary.execute_console_command(world, "r.HighResScreenshotDelay 24")
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()

started = time.monotonic()
capture_started = None
tick_handle = None


def finish(ok: bool, reason: str) -> None:
    global tick_handle
    (unreal.log if ok else unreal.log_error)(
        f"LINE_BOSS_PR005_HMI_QA_CAPTURE_V002_{'PASS' if ok else 'FAIL'} {reason}"
    )
    if tick_handle is not None:
        unreal.unregister_slate_post_tick_callback(tick_handle)
        tick_handle = None
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.execute_console_command(world, "QUIT_EDITOR")


def tick(_delta: float) -> None:
    global capture_started
    now = time.monotonic()
    if capture_started is None and now - started >= 5.0:
        task = unreal.AutomationLibrary.take_high_res_screenshot(
            1920,
            1080,
            str(OUT),
            camera=camera,
            mask_enabled=False,
            capture_hdr=False,
            comparison_tolerance=unreal.ComparisonTolerance.LOW,
            comparison_notes="PR005 detailed Meshy HMI robust fixed-camera QA",
            delay=15.0,
            force_game_view=True,
        )
        if not task.is_valid_task():
            finish(False, "invalid screenshot task")
            return
        capture_started = now
        unreal.log(f"LINE_BOSS_PR005_HMI_QA_CAPTURE_V002_REQUESTED output={OUT}")
    elif capture_started is not None and OUT.exists() and OUT.stat().st_size >= 100000:
        finish(True, str(OUT))
    elif now - started > 100.0:
        finish(False, "timed out waiting for a non-placeholder PNG")


tick_handle = unreal.register_slate_post_tick_callback(tick)
