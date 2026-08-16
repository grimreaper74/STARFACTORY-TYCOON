"""Capture the actual native MR01 parked presentation in isolated v013 PIE.

This script does not save the map or any asset. It waits for BeginPlay/Tick to
bind the v022 poseable arm, then records exact component bounds and a fixed
camera screenshot from the PIE world.
"""

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time

import unreal


unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP = "/Game/LineBoss/Developer/Validation/LB_ServiceDockActualRobotFit_v013"
ACTOR_LABEL = "LB_DOCK_FIT_MR01_v022_ActualAuthority"
CAMERA_LABEL = "LB_DOCK_FIT_CAM_MR01_Oblique"
ROOT = Path(unreal.Paths.project_dir())
OUT = ROOT / "Saved/ValidationScreenshots/SupportRobots/ServiceDocks/ActualRobotFit_v013/service_dock_actual_robot_fit_v013_mr01_runtime_parked.png"
AUDIT = ROOT / "Saved/Audits/SupportRobots/service_dock_mr01_runtime_parked_v015.json"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError("Could not load {}".format(MAP))
OUT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.parent.mkdir(parents=True, exist_ok=True)
if OUT.exists():
    OUT.unlink()

unreal.EditorLevelLibrary.editor_play_simulate()
started = time.monotonic()
capture_started = None
handle = None
evidence = {}
test_pose_text = os.environ.get("LB_MR01_TEST_POSE", "").strip()
capture_revision = os.environ.get("LB_MR01_CAPTURE_REV", "").strip()
test_pose = [float(value) for value in test_pose_text.split(",")] if test_pose_text else None
if test_pose is not None and len(test_pose) != 6:
    raise RuntimeError("LB_MR01_TEST_POSE must contain exactly six comma-separated degrees")
if test_pose is not None:
    pose_slug = "_".join(str(int(value)).replace("-", "m") for value in test_pose)
    OUT = OUT.with_name("service_dock_actual_robot_fit_v013_mr01_runtime_test_pose_{}.png".format(pose_slug))
    AUDIT = AUDIT.with_name("service_dock_mr01_runtime_test_pose_{}_v018.json".format(pose_slug))
elif capture_revision:
    OUT = OUT.with_name("service_dock_actual_robot_fit_v013_mr01_runtime_parked_{}.png".format(capture_revision))
    AUDIT = AUDIT.with_name("service_dock_mr01_runtime_parked_{}.json".format(capture_revision))
pose_applied = False


def vec(value):
    return [round(float(value.x), 4), round(float(value.y), 4), round(float(value.z), 4)]


def finish(success, detail):
    global handle
    if OUT.exists():
        evidence["screenshot_sha256"] = hashlib.sha256(OUT.read_bytes()).hexdigest().upper()
        evidence["screenshot_bytes"] = OUT.stat().st_size
    evidence.update({
        "$schema": "cairnwell/audit/service-dock-mr01-runtime-parked-v015/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS__LIVE_PIE_PARKED_POSE_CAPTURED__VISUAL_REVIEW_REQUIRED__NOT_PROMOTED" if success else "FAIL__LIVE_PIE_PARKED_POSE_NOT_PROVED__NOT_PROMOTED",
        "map": MAP,
        "actor": ACTOR_LABEL,
        "detail": detail,
        "map_saved": False,
        "promotion_authorized": False,
    })
    AUDIT.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    (unreal.log if success else unreal.log_error)("LINE_BOSS_MR01_RUNTIME_PARKED_V015 {} {}".format("PASS" if success else "FAIL", detail))
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.SystemLibrary.quit_editor()


def tick(_delta_seconds):
    global capture_started, pose_applied
    now = time.monotonic()
    if now - started > 65.0:
        finish(False, "timeout")
        return
    world = unreal.EditorLevelLibrary.get_game_world()
    if world is None:
        return
    actors = [a for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBMaintenanceAMR)
              if a.get_actor_label() == ACTOR_LABEL]
    cameras = [a for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.CameraActor)
               if a.get_actor_label() == CAMERA_LABEL]
    if len(actors) != 1 or len(cameras) != 1:
        if now - started > 10.0:
            finish(False, "actors={} cameras={}".format(len(actors), len(cameras)))
        return
    robot = actors[0]
    arm = None
    collision = None
    for component in robot.get_components_by_class(unreal.SceneComponent):
        tags = {str(tag) for tag in component.get_editor_property("component_tags")}
        if isinstance(component, unreal.PoseableMeshComponent) and "LB.MR01.ArmPoseable" in tags:
            arm = component
        elif component.get_name().startswith("RP01_CollisionRoot"):
            collision = component
    if arm is None or collision is None:
        if now - started > 10.0:
            finish(False, "runtime arm/collision missing")
        return
    if test_pose is not None and not pose_applied:
        state = robot.capture_save_state()
        common = state.common
        common.unit_id = unreal.Name("MR01-POSE-CAPTURE")
        common.variant_id = unreal.Name("LB-MR01")
        state.common = common
        state.arm_joint_degrees = test_pose
        state.arm_lift_millimetres = 0.0
        state.arm_parked = False
        if not robot.restore_save_state(state):
            finish(False, "native candidate-pose restore rejected")
            return
        pose_applied = True
        evidence["transient_test_pose_deg"] = test_pose
        evidence["transient_test_identity"] = "MR01-POSE-CAPTURE"
        return
    if capture_started is None:
        # Allow BeginPlay plus several native ticks to cache and apply the pose.
        if now - started < (5.0 if test_pose is not None else 3.0):
            return
        arm_origin, arm_extent, _ = unreal.SystemLibrary.get_component_bounds(arm)
        collision_origin, collision_extent, _ = unreal.SystemLibrary.get_component_bounds(collision)
        evidence["arm_bounds_origin_cm"] = vec(arm_origin)
        evidence["arm_bounds_size_cm"] = vec(arm_extent * 2.0)
        evidence["collision_bounds_origin_cm"] = vec(collision_origin)
        evidence["collision_bounds_size_cm"] = vec(collision_extent * 2.0)
        evidence["tcp_world_cm"] = vec(arm.get_socket_location(unreal.Name("tcp")))
        bone_names = ("root", "lift", "j1_base", "j2_shoulder", "j3_elbow",
                      "j4_wrist_roll", "j5_wrist_pitch", "j6_tool_roll",
                      "tool_coupler", "tcp")
        evidence["runtime_bones_component_cm"] = {
            name: vec(arm.get_bone_transform_by_name(
                unreal.Name(name), unreal.BoneSpaces.COMPONENT_SPACE).translation)
            for name in bone_names
        }
        unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
        unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
        unreal.EditorLevelLibrary.editor_set_game_view(True)
        unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
        unreal.AutomationLibrary.finish_loading_before_screenshot()
        task = unreal.AutomationLibrary.take_high_res_screenshot(
            1920, 1080, str(OUT), camera=cameras[0], force_game_view=True,
            comparison_tolerance=unreal.ComparisonTolerance.LOW,
            comparison_notes="MR01 v022 straight-reverse dock live parked pose v015")
        if not task.is_valid_task():
            finish(False, "invalid screenshot task")
            return
        capture_started = now
        return
    if now - capture_started >= 3.0 and OUT.exists() and OUT.stat().st_size >= 1024:
        finish(True, "live PIE screenshot and bounds recorded")
    elif now - capture_started > 50.0:
        finish(False, "screenshot missing")


handle = unreal.register_slate_post_tick_callback(tick)
