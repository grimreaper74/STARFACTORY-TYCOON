"""Capture one live-PIE fixed view of the installed v255 support fleet."""

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time

import unreal


unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v255"
VIEWS = {
    "mr01": "LB_SUPPORT_FLEET_CAM_MR01_v255",
    "cr01": "LB_SUPPORT_FLEET_CAM_CR01_v255",
    "overview": "LB_SUPPORT_FLEET_CAM_OVERVIEW_v255",
}
capture_id = os.environ.get("LB_SUPPORT_FLEET_CAPTURE", "mr01").strip().lower()
if capture_id not in VIEWS:
    raise RuntimeError(f"Unknown support-fleet capture {capture_id}")

ROOT = Path(unreal.Paths.project_dir())
OUT = ROOT / "Saved/ValidationScreenshots/SupportRobots/PressShopFleet_v255" / f"press_shop_support_fleet_v255_{capture_id}.png"
AUDIT = ROOT / "Saved/Audits/SupportRobots" / f"press_shop_support_fleet_runtime_capture_v255_{capture_id}.json"
LEVELS = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not LEVELS.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
OUT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.parent.mkdir(parents=True, exist_ok=True)
if OUT.exists():
    OUT.unlink()

unreal.EditorLevelLibrary.editor_play_simulate()
started = time.monotonic()
capture_started = None
handle = None
evidence = {}


def finish(success, detail):
    global handle
    if OUT.exists():
        evidence["screenshot_sha256"] = hashlib.sha256(OUT.read_bytes()).hexdigest().upper()
        evidence["screenshot_bytes"] = OUT.stat().st_size
    evidence.update({
        "$schema": "cairnwell/audit/press-shop-support-fleet-runtime-capture-v255/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS__FOUR_LIVE_DOCKED_AUTHORITIES_CAPTURED__VISUAL_REVIEW_REQUIRED__NOT_PROMOTED" if success else "FAIL__LIVE_SUPPORT_FLEET_CAPTURE__NOT_RETAINED",
        "map": MAP,
        "capture": capture_id,
        "camera": VIEWS[capture_id],
        "detail": detail,
        "map_saved": False,
        "promotion_authorized": False,
    })
    AUDIT.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    (unreal.log if success else unreal.log_error)(f"LINE_BOSS_SUPPORT_FLEET_V255_CAPTURE {'PASS' if success else 'FAIL'} {capture_id} {detail}")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.SystemLibrary.quit_editor()


def tick(_delta_seconds):
    global capture_started
    now = time.monotonic()
    if now - started > 75.0:
        finish(False, "timeout")
        return
    world = unreal.EditorLevelLibrary.get_game_world()
    if world is None:
        return
    mr_actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBMaintenanceAMR)
    cr_actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBCleaningAMR)
    cameras = [actor for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.CameraActor)
               if actor.get_actor_label() == VIEWS[capture_id]]
    if len(mr_actors) != 2 or len(cr_actors) != 2 or len(cameras) != 1:
        if now - started > 12.0:
            finish(False, f"MR01={len(mr_actors)} CR01={len(cr_actors)} cameras={len(cameras)}")
        return
    robots = sorted(mr_actors + cr_actors, key=lambda actor: actor.get_actor_label())
    if capture_started is None:
        if now - started < 4.0:
            return
        robot_rows = []
        for robot in robots:
            state = robot.capture_common_save_state()
            robot_rows.append({
                "actor": robot.get_actor_label(),
                "unit_id": str(state.unit_id),
                "variant_id": str(state.variant_id),
                "docked": bool(state.docked),
                "dock_id": str(state.dock_id),
                "state": str(state.state),
            })
        if len({row["unit_id"] for row in robot_rows}) != 4:
            finish(False, "unit identities are not unique")
            return
        if not all(row["docked"] and row["dock_id"] not in ("", "None") for row in robot_rows):
            finish(False, "one or more live robots lost dock authority")
            return
        evidence["robots"] = robot_rows
        unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
        unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
        unreal.SystemLibrary.execute_console_command(world, "r.HighResScreenshotDelay 24")
        unreal.EditorLevelLibrary.editor_set_game_view(True)
        unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
        unreal.AutomationLibrary.finish_loading_before_screenshot()
        task = unreal.AutomationLibrary.take_high_res_screenshot(
            1920, 1080, str(OUT), camera=cameras[0], mask_enabled=False,
            capture_hdr=False, comparison_tolerance=unreal.ComparisonTolerance.LOW,
            comparison_notes=f"Press Shop v255 live support fleet {capture_id}",
            delay=0.0, force_game_view=True)
        if not task.is_valid_task():
            finish(False, "invalid screenshot task")
            return
        capture_started = now
        return
    if now - capture_started >= 3.0 and OUT.exists() and OUT.stat().st_size >= 1024:
        finish(True, "live PIE fleet identities, dock authority and screenshot recorded")
    elif now - capture_started > 55.0:
        finish(False, "screenshot missing")


handle = unreal.register_slate_post_tick_callback(tick)
