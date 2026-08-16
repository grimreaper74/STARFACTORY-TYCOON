"""Capture live v269 MR01 at certified standby, then return it safely."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time

import unreal


unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v269"
ROOT = Path(unreal.Paths.project_dir())
OUT = ROOT / "Saved/ValidationScreenshots/SupportRobots/PressShopFleet_v269/press_shop_support_fleet_v269_mr01_dispatched_standby.png"
AUDIT = ROOT / "Saved/Audits/SupportRobots/press_shop_support_fleet_dispatch_runtime_capture_v269.json"
LEVELS = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not LEVELS.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
OUT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.parent.mkdir(parents=True, exist_ok=True)
if OUT.exists():
    OUT.unlink()
unreal.EditorLevelLibrary.editor_play_simulate()
started = time.monotonic()
phase_started = started
phase = "wait_ready"
camera = None
task = None
handle = None


def finish(success, detail, robot=None):
    global handle
    payload = {
        "$schema": "cairnwell/audit/press-shop-support-fleet-dispatch-runtime-capture-v269/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS__LIVE_CERTIFIED_DISPATCH_CAPTURED_AND_ROBOT_RETURNED__VISUAL_REVIEW_REQUIRED__NOT_PROMOTED"
                  if success else "FAIL__DISPATCH_CAPTURE__NOT_RETAINED",
        "map": MAP, "detail": detail, "map_saved": False, "promotion_authorized": False,
    }
    if robot:
        saved = robot.capture_common_save_state()
        payload["final_robot"] = {"unit_id": str(saved.unit_id), "state": str(saved.state),
                                  "docked": bool(saved.docked), "dock_id": str(saved.dock_id)}
    if OUT.exists():
        payload["screenshot"] = str(OUT.relative_to(ROOT)).replace("\\", "/")
        payload["screenshot_sha256"] = hashlib.sha256(OUT.read_bytes()).hexdigest().upper()
        payload["screenshot_bytes"] = OUT.stat().st_size
    AUDIT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.SystemLibrary.quit_editor()


def tick(_delta):
    global phase, phase_started, camera, task
    now = time.monotonic()
    if now - started > 240.0:
        finish(False, f"timeout in {phase}")
        return
    world = unreal.EditorLevelLibrary.get_game_world()
    if world is None:
        return
    controllers = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBPressShopSupportFleetController)
    robots = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBMaintenanceAMR)
    robot = next((item for item in robots if str(item.capture_common_save_state().unit_id) == "LB-MR01-01"), None)
    if len(controllers) != 1 or robot is None:
        return
    controller = controllers[0]
    if phase == "wait_ready":
        if not controller.is_fleet_ready():
            return
        unreal.SystemLibrary.execute_console_command(world, "slomo 20")
        if not controller.dispatch_unit(unreal.Name("LB-MR01-01")):
            finish(False, "dispatch refused", robot); return
        phase = "wait_standby"; phase_started = now; return
    if phase == "wait_standby":
        saved = robot.capture_common_save_state()
        if str(saved.active_fault) not in ("<LBSupportRobotFault.NONE: 0>", "LBSupportRobotFault.NONE"):
            finish(False, f"dispatch fault {robot.get_last_common_fault_detail()}", robot); return
        if ((robot.get_actor_location().x + 6495.0) ** 2
                + (robot.get_actor_location().y - 5160.0) ** 2) ** 0.5 < 500.0:
            return
        robot_position = robot.get_actor_location()
        position = unreal.Vector(robot_position.x - 850.0, robot_position.y - 900.0, 590.0)
        camera = unreal.GameplayStatics.begin_deferred_actor_spawn_from_class(
            world, unreal.CameraActor, unreal.Transform(location=position))
        camera = unreal.GameplayStatics.finish_spawning_actor(camera, unreal.Transform(location=position))
        camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
            position, unreal.Vector(robot_position.x, robot_position.y, 70.0)), False)
        camera.camera_component.set_editor_properties({"field_of_view": 68.0, "aspect_ratio": 16.0 / 9.0,
                                                       "constrain_aspect_ratio": True})
        unreal.SystemLibrary.execute_console_command(world, "slomo 1")
        unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
        unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
        unreal.EditorLevelLibrary.editor_set_game_view(True)
        unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
        unreal.AutomationLibrary.finish_loading_before_screenshot()
        task = unreal.AutomationLibrary.take_high_res_screenshot(
            1920, 1080, str(OUT), camera=camera, mask_enabled=False, capture_hdr=False,
            comparison_tolerance=unreal.ComparisonTolerance.LOW,
            comparison_notes="v269 MR01 live certified dispatch in motion near service bay",
            delay=0.0, force_game_view=True)
        if not task.is_valid_task():
            finish(False, "invalid screenshot task", robot); return
        phase = "wait_capture"; phase_started = now; return
    if phase == "wait_capture":
        if not OUT.exists() or OUT.stat().st_size < 1024:
            if now - phase_started > 45.0:
                finish(False, "screenshot missing", robot)
            return
        unreal.SystemLibrary.execute_console_command(world, "slomo 20")
        phase = "wait_outbound_complete"; phase_started = now; return
    if phase == "wait_outbound_complete":
        if robot.has_route_authority():
            return
        if not controller.return_unit_to_dock(unreal.Name("LB-MR01-01")):
            finish(False, "return refused after outbound completion", robot); return
        phase = "wait_return"; phase_started = now; return
    if phase == "wait_return":
        saved = robot.capture_common_save_state()
        if robot.has_route_authority() or not bool(saved.docked):
            return
        finish(True, "live MR01 certified-route motion captured and robot returned to its own charging dock", robot)


handle = unreal.register_slate_post_tick_callback(tick)
