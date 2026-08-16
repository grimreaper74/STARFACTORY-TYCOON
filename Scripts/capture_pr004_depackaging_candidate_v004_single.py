"""Request one deterministic PR-004 Candidate_v004 screenshot per session."""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import unreal


REPO = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Developer/Validation/PR004/LB_PR004_Depackaging_Candidate_v004"
CAMERAS = {
    "overview_sw": "LB_PR004_CAM_Overview_SW",
    "overview_ne": "LB_PR004_CAM_Overview_NE",
    "top": "LB_PR004_CAM_Top",
    "cradle_close": "LB_PR004_CAM_CradleClose",
    "robot_tools": "LB_PR004_CAM_RobotTools",
    "packaging_close": "LB_PR004_CAM_PackagingClose",
    "film_dewrap": "LB_PR004_CAM_FilmDewrap",
}
CAPTURE_ID = os.environ.get("LB_PR004_CAPTURE_ID", "")
if CAPTURE_ID not in CAMERAS:
    raise RuntimeError(f"Set LB_PR004_CAPTURE_ID to one of {sorted(CAMERAS)}")

OUT = REPO / "Saved/ValidationScreenshots/PR004/Candidate_v004"
MARKER = REPO / f"Saved/Audits/pr004_capture_marker_{CAPTURE_ID}_v004.json"
OUT.mkdir(parents=True, exist_ok=True)
output = OUT / f"pr004_candidate_v004_{CAPTURE_ID}_pbr.png"
if output.exists():
    output.unlink()

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
camera = next(
    (actor for actor in actors.get_all_level_actors() if actor.get_actor_label() == CAMERAS[CAPTURE_ID]),
    None,
)
if camera is None:
    raise RuntimeError(f"Missing fixed camera {CAMERAS[CAPTURE_ID]}")

world = unreal.EditorLevelLibrary.get_editor_world()
unreal.AutomationLibrary.set_editor_viewport_view_mode(unreal.ViewModeIndex.VMI_LIT)
unreal.AutomationLibrary.set_editor_active_viewport_view_mode(unreal.ViewModeIndex.VMI_LIT)
unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()
unreal.AutomationLibrary.set_editor_viewport_view_mode(unreal.ViewModeIndex.VMI_LIT)
unreal.AutomationLibrary.set_editor_active_viewport_view_mode(unreal.ViewModeIndex.VMI_LIT)
unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
unreal.SystemLibrary.execute_console_command(world, "showflag.Materials 1")
unreal.SystemLibrary.execute_console_command(world, "showflag.Lighting 1")
unreal.SystemLibrary.execute_console_command(world, "showflag.Diffuse 1")
unreal.SystemLibrary.execute_console_command(world, "showflag.Specular 1")

started = time.monotonic()
task = unreal.AutomationLibrary.take_high_res_screenshot(
    1920,
    1080,
    str(output),
    camera=camera,
    mask_enabled=False,
    capture_hdr=False,
    comparison_tolerance=unreal.ComparisonTolerance.LOW,
    comparison_notes=f"Line Boss PR-004 Candidate_v004 PBR fixed review: {CAPTURE_ID}",
    delay=1.0,
    force_game_view=True,
)
if not task.is_valid_task():
    raise RuntimeError(f"Unreal did not create screenshot task for {CAPTURE_ID}")

tick_handle = None
MARKER.parent.mkdir(parents=True, exist_ok=True)
MARKER.write_text(json.dumps({
    "$schema": "line-boss/audit/pr004-unreal-single-capture-marker-v004/v1",
    "requested_utc": datetime.now(timezone.utc).isoformat(),
    "capture_id": CAPTURE_ID,
    "camera": CAMERAS[CAPTURE_ID],
    "path": str(output),
    "status": "SCREENSHOT_REQUEST_ACCEPTED__FILE_MUST_BE_VERIFIED_EXTERNALLY",
    "promotion": "FORBIDDEN",
}, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR004_V004_SCREENSHOT_REQUESTED id={CAPTURE_ID} path={output}")


def finish_when_ready(_delta_seconds):
    global tick_handle
    elapsed = time.monotonic() - started
    # UE can report the screenshot task complete one or two ticks before the
    # render target has been encoded and written.  Never quit on that transient
    # state: require a short render window and the actual output file.
    if elapsed < 3.0:
        return
    if task.is_task_done() and not output.exists() and elapsed < 45.0:
        return
    if not task.is_task_done() and elapsed < 45.0:
        return
    passed = output.exists() and output.stat().st_size >= 1024
    MARKER.write_text(json.dumps({
        "$schema": "line-boss/audit/pr004-unreal-single-capture-marker-v004/v1",
        "completed_utc": datetime.now(timezone.utc).isoformat(),
        "capture_id": CAPTURE_ID,
        "camera": CAMERAS[CAPTURE_ID],
        "path": str(output),
        "bytes": output.stat().st_size if output.exists() else 0,
        "elapsed_seconds": round(elapsed, 3),
        "status": "CAPTURE_PASS__VISUAL_REVIEW_REQUIRED__CANDIDATE_NOT_PROMOTED" if passed else "CAPTURE_FAIL__CANDIDATE_NOT_PROMOTED",
        "promotion": "FORBIDDEN",
    }, indent=2), encoding="utf-8")
    if passed:
        unreal.log(f"LINE_BOSS_PR004_V004_SCREENSHOT_PASS id={CAPTURE_ID} path={output}")
    else:
        unreal.log_error(f"LINE_BOSS_PR004_V004_SCREENSHOT_FAIL id={CAPTURE_ID} path={output}")
    if tick_handle is not None:
        unreal.unregister_slate_post_tick_callback(tick_handle)
        tick_handle = None
    unreal.SystemLibrary.quit_editor()


tick_handle = unreal.register_slate_post_tick_callback(finish_when_ready)
