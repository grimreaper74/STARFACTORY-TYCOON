"""Capture a fresh close rendered PIE view of the v269 fleet controls/status row."""

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import unreal


unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v269"
ROOT = Path(unreal.Paths.project_dir())
OUT = ROOT / "Saved/ValidationScreenshots/ControlRoom/v269_support_fleet/press_shop_v269_support_fleet_screen_close.png"
AUDIT = ROOT / "Saved/Audits/ControlRoom/control_room_support_fleet_screen_capture_v269.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
OUT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.parent.mkdir(parents=True, exist_ok=True)
if OUT.exists():
    OUT.unlink()
unreal.EditorLevelLibrary.editor_play_simulate()
started = time.monotonic()
capture_started = None
handle = None
camera = None
CAMERA_LABEL = "LB_WHOLE_V224_CAM_ControlRoomWalkUp"


def finish(success, detail):
    global handle
    evidence = {
        "$schema": "cairnwell/audit/control-room-support-fleet-screen-capture-v269/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS__FRESH_RENDER_RECORDED__VISUAL_REVIEW_REQUIRED__NOT_PROMOTED" if success
                  else "FAIL__CONTROL_ROOM_FLEET_SCREEN_CAPTURE__NOT_RETAINED",
        "map": MAP,
        "detail": detail,
        "map_saved": False,
        "promotion_authorized": False,
    }
    if OUT.exists():
        evidence["screenshot"] = str(OUT.relative_to(ROOT)).replace("\\", "/")
        evidence["screenshot_bytes"] = OUT.stat().st_size
        evidence["screenshot_sha256"] = hashlib.sha256(OUT.read_bytes()).hexdigest().upper()
    AUDIT.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    (unreal.log if success else unreal.log_error)(f"LINE_BOSS_CONTROL_ROOM_FLEET_SCREEN_V269 {'PASS' if success else 'FAIL'} {detail}")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.SystemLibrary.quit_editor()


def tick(_delta):
    global capture_started, camera
    now = time.monotonic()
    if now - started > 90.0:
        finish(False, "timeout")
        return
    world = unreal.EditorLevelLibrary.get_game_world()
    if not world:
        return
    consoles = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBControlRoomOperationsConsole)
    fleets = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBPressShopSupportFleetController)
    if len(consoles) != 1 or len(fleets) != 1 or not fleets[0].is_fleet_ready():
        return
    if capture_started is None:
        cameras = [actor for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.CameraActor)
                   if actor.get_actor_label() == CAMERA_LABEL]
        if len(cameras) != 1:
            finish(False, f"authored walk-up camera count {len(cameras)}")
            return
        camera = cameras[0]
        unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
        unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
        unreal.SystemLibrary.execute_console_command(world, "r.HighResScreenshotDelay 28")
        unreal.EditorLevelLibrary.editor_set_game_view(True)
        unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
        unreal.AutomationLibrary.finish_loading_before_screenshot()
        task = unreal.AutomationLibrary.take_high_res_screenshot(
            1920, 1080, str(OUT), camera=camera, mask_enabled=False, capture_hdr=False,
            comparison_tolerance=unreal.ComparisonTolerance.LOW,
            comparison_notes="Press Shop v269 support fleet control-room screen close",
            delay=0.0, force_game_view=True)
        if not task.is_valid_task():
            finish(False, "invalid screenshot task")
            return
        capture_started = now
        return
    if now - capture_started > 3.0 and OUT.exists() and OUT.stat().st_size >= 1024:
        finish(True, "live fleet-ready operations console captured")
    elif now - capture_started > 65.0:
        finish(False, "screenshot missing")


handle = unreal.register_slate_post_tick_callback(tick)
