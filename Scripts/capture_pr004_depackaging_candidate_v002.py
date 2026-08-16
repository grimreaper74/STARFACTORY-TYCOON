"""Capture fresh fixed-camera Unreal evidence for PR-004 Candidate_v002.

Run through UnrealEditor.exe (not the Python commandlet) so Slate can tick the
latent high-resolution screenshot tasks.  The script quits the temporary
editor automatically after all seven files are verified.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Developer/Validation/PR004/LB_PR004_Depackaging_Candidate_v002"
CAPTURES = (
    ("overview_sw", "LB_PR004_CAM_Overview_SW"),
    ("overview_ne", "LB_PR004_CAM_Overview_NE"),
    ("top", "LB_PR004_CAM_Top"),
    ("cradle_close", "LB_PR004_CAM_CradleClose"),
    ("robot_tools", "LB_PR004_CAM_RobotTools"),
    ("packaging_close", "LB_PR004_CAM_PackagingClose"),
    ("film_dewrap", "LB_PR004_CAM_FilmDewrap"),
)
ROOT = Path(unreal.Paths.project_saved_dir())
OUT = ROOT / "ValidationScreenshots/PR004/Candidate_v002"
AUDIT = ROOT / "Audits/pr004_unreal_capture_candidate_v002.json"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
camera_by_label = {actor.get_actor_label(): actor for actor in actors.get_all_level_actors()}
missing = [label for _, label in CAPTURES if label not in camera_by_label]
if missing:
    raise RuntimeError(f"Missing fixed PR-004 cameras: {missing}")

OUT.mkdir(parents=True, exist_ok=True)
world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
unreal.SystemLibrary.execute_console_command(world, "r.ForceDebugViewModes 0")
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()

pending = list(CAPTURES)
records = []
active = None
active_started = 0.0
next_ready = 0.0
tick_handle = None


def start_next():
    global active, active_started
    capture_id, camera_label = pending.pop(0)
    output = OUT / f"pr004_candidate_v002_{capture_id}_final.png"
    if output.exists():
        output.unlink()
    unreal.AutomationLibrary.finish_loading_before_screenshot()
    task = unreal.AutomationLibrary.take_high_res_screenshot(
        1920,
        1080,
        str(output),
        camera=camera_by_label[camera_label],
        mask_enabled=False,
        capture_hdr=False,
        comparison_tolerance=unreal.ComparisonTolerance.LOW,
        comparison_notes=f"Line Boss PR-004 Candidate_v002 fixed review: {capture_id}",
        delay=0.0,
        force_game_view=True,
    )
    if not task.is_valid_task():
        raise RuntimeError(f"Unreal did not create screenshot task for {capture_id}")
    active = (capture_id, camera_label, output, task)
    active_started = time.monotonic()
    unreal.log(f"LINE_BOSS_PR004_SCREENSHOT_REQUESTED id={capture_id} path={output}")


def on_tick(_delta_seconds):
    global active, next_ready, tick_handle
    now = time.monotonic()
    if active is None:
        if now < next_ready:
            return
        if pending:
            start_next()
            return
        passed = len(records) == len(CAPTURES) and all(record["status"] == "CAPTURE_PASS" for record in records)
        result = {
            "$schema": "line-boss/audit/pr004-unreal-capture-v002/v1",
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "status": "FRESH_UNREAL_SCREENSHOTS_CAPTURED__VISUAL_REVIEW_REQUIRED__CANDIDATE_NOT_PROMOTED" if passed else "UNREAL_SCREENSHOT_CAPTURE_FAIL__CANDIDATE_NOT_PROMOTED",
            "engine_version": str(unreal.SystemLibrary.get_engine_version()),
            "map": MAP,
            "resolution": [1920, 1080],
            "captures": records,
            "visual_gate_passed": False,
            "promotion": "FORBIDDEN",
        }
        AUDIT.parent.mkdir(parents=True, exist_ok=True)
        AUDIT.write_text(json.dumps(result, indent=2), encoding="utf-8")
        if passed:
            unreal.log(f"LINE_BOSS_PR004_CAPTURE_PASS count={len(records)} dir={OUT} audit={AUDIT}")
        else:
            unreal.log_error(f"LINE_BOSS_PR004_CAPTURE_FAIL count={len(records)} audit={AUDIT}")
        if tick_handle is not None:
            unreal.unregister_slate_post_tick_callback(tick_handle)
            tick_handle = None
        unreal.SystemLibrary.quit_editor()
        return

    capture_id, camera_label, output, task = active
    elapsed = now - active_started
    if not task.is_task_done() and elapsed < 45.0:
        return
    passed = output.exists() and output.stat().st_size >= 1024
    records.append({
        "id": capture_id,
        "camera": camera_label,
        "path": str(output),
        "bytes": output.stat().st_size if output.exists() else 0,
        "elapsed_seconds": round(elapsed, 3),
        "status": "CAPTURE_PASS" if passed else "CAPTURE_FAIL",
    })
    if not passed:
        unreal.log_error(f"LINE_BOSS_PR004_SCREENSHOT_FAIL id={capture_id} path={output}")
    active = None
    next_ready = now + 0.35


tick_handle = unreal.register_slate_post_tick_callback(on_tick)
