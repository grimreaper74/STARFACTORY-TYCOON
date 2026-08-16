"""Capture every fixed PR-001--PR-005 review camera in one Unreal session."""

from __future__ import annotations

import json
import time
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_IntegrationCandidate_v002"
ROOT = Path(unreal.Paths.project_saved_dir())
OUTPUT_DIR = ROOT / "ValidationScreenshots/PressShopIntegration"
AUDIT = ROOT / "Audits/press_shop_front_end_capture_batch_v002.json"
CAPTURES = [
    ("front_end_overview", "LB_INT_FRONT_CAM_FrontEndOverview", "press_shop_front_end_overview_v002.png"),
    ("coil_store_crane", "LB_INT_FRONT_CAM_CoilStoreCrane", "press_shop_coil_store_crane_v002.png"),
    ("pr001_pr002", "LB_INT_FRONT_CAM_PR001_PR002", "press_shop_pr001_pr002_v002.png"),
    ("crane_detail", "LB_INT_FRONT_CAM_CraneDetail", "press_shop_crane_detail_v002.png"),
    ("pr004_prep", "LB_INT_FRONT_CAM_PR004Prep", "press_shop_pr004_prep_v002.png"),
    ("front_eye", "LB_INT_FRONT_CAM_FrontEndEyeLevel", "press_shop_front_end_eye_level_v002.png"),
    ("front_top", "LB_INT_FRONT_CAM_FrontEndTop", "press_shop_front_end_top_v002.png"),
]

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actor_system = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels.load_level(MAP)
camera_by_label = {actor.get_actor_label(): actor for actor in actor_system.get_all_level_actors()}
missing = [camera_label for _, camera_label, _ in CAPTURES if camera_label not in camera_by_label]
if missing:
    raise RuntimeError(f"Missing fixed front-end cameras: {missing}")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
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
    capture_id, camera_label, filename = pending.pop(0)
    output = OUTPUT_DIR / filename
    if output.exists():
        output.unlink()
    unreal.AutomationLibrary.finish_loading_before_screenshot()
    task = unreal.AutomationLibrary.take_high_res_screenshot(
        1920, 1080, str(output), camera=camera_by_label[camera_label],
        mask_enabled=False, capture_hdr=False,
        comparison_tolerance=unreal.ComparisonTolerance.LOW,
        comparison_notes=f"Line Boss front-end fixed review: {capture_id}",
        delay=0.0, force_game_view=True,
    )
    if not task.is_valid_task():
        raise RuntimeError(f"Unreal did not create screenshot task for {capture_id}")
    active = (capture_id, camera_label, output, task)
    active_started = time.monotonic()
    unreal.log(f"LINE_BOSS_FRONT_END_BATCH_SCREENSHOT_REQUESTED id={capture_id} path={output}")


def on_tick(_delta_seconds):
    global active, next_ready, tick_handle
    now = time.monotonic()
    if active is None:
        if now < next_ready:
            return
        if pending:
            start_next()
            return
        AUDIT.parent.mkdir(parents=True, exist_ok=True)
        AUDIT.write_text(json.dumps({
            "status": "FRESH_FIXED_CAMERA_CAPTURE_PASS",
            "map": MAP,
            "capture_count": len(records),
            "records": records,
            "visual_promotion": "NOT_IMPLIED",
        }, indent=2), encoding="utf-8")
        unreal.log(f"LINE_BOSS_FRONT_END_BATCH_SCREENSHOT_PASS count={len(records)} audit={AUDIT}")
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
        unreal.log_error(f"LINE_BOSS_FRONT_END_BATCH_SCREENSHOT_FAIL id={capture_id} path={output}")
    active = None
    next_ready = now + 0.35


tick_handle = unreal.register_slate_post_tick_callback(on_tick)
