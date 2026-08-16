"""Frame-stepped native PIE search for a compact MR01 parked-arm pose.

One candidate is applied per Slate frame and measured on the following frame so
PoseableMesh render/bounds data is authoritative. No map or asset is saved.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
import time

import unreal


unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP = "/Game/LineBoss/Developer/Validation/LB_ServiceDockActualRobotFit_v013"
ACTOR_LABEL = "LB_DOCK_FIT_MR01_v022_ActualAuthority"
ROOT = Path(unreal.Paths.project_dir())
OUT = ROOT / "Saved/Audits/SupportRobots/mr01_frame_stepped_parked_pose_search_v019.json"
OUT.parent.mkdir(parents=True, exist_ok=True)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
unreal.EditorLevelLibrary.editor_play_simulate()

poses = [
    [float(j1), float(j2), float(j3), 0.0, -95.0, 0.0]
    for j1 in (180, 135, 90, 45, 0, -45, -90)
    for j2 in (-95, -75, -55, -35, -15, 5, 25, 45, 65, 85, 105)
    for j3 in (-145, -120, -95, -70, -45, -20, 5, 30, 55, 80, 105, 130, 150)
]
started = time.monotonic()
handle = None
robot = arm = collision = cradle = None
collision_origin = collision_extent = collision_min = collision_max = cradle_world = None
pending_pose = None
next_index = 0
rows = []
restore_failures = 0


def vec(value):
    return [round(float(value.x), 4), round(float(value.y), 4), round(float(value.z), 4)]


def finish(status):
    global handle
    rows.sort(key=lambda row: row["score"])
    OUT.write_text(json.dumps({
        "$schema": "cairnwell/audit/mr01-frame-stepped-parked-pose-search-v019/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "source_map_played_not_saved": MAP,
        "actor": ACTOR_LABEL,
        "candidate_count_requested": len(poses),
        "candidate_count_measured": len(rows),
        "restore_failures": restore_failures,
        "collision_bounds_origin_cm": vec(collision_origin) if collision_origin else None,
        "collision_bounds_size_cm": vec(collision_extent * 2.0) if collision_extent else None,
        "parking_cradle_world_cm": vec(cradle_world) if cradle_world else None,
        "best_candidates": rows[:100],
        "map_saved": False,
        "promotion_authorized": False,
    }, indent=2) + "\n", encoding="utf-8")
    unreal.log("LINE_BOSS_MR01_FRAME_STEPPED_POSE_V019 {} measured={}".format(status, len(rows)))
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.SystemLibrary.quit_editor()


def tick(_delta_seconds):
    global robot, arm, collision, cradle, collision_origin, collision_extent
    global collision_min, collision_max, cradle_world, pending_pose, next_index, restore_failures
    if time.monotonic() - started > 100.0:
        finish("FAIL__FRAME_STEPPED_SEARCH_TIMEOUT__NOT_PROMOTED")
        return
    world = unreal.EditorLevelLibrary.get_game_world()
    if world is None or time.monotonic() - started < 3.0:
        return
    if robot is None:
        robots = [a for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBMaintenanceAMR)
                  if a.get_actor_label() == ACTOR_LABEL]
        if len(robots) != 1:
            return
        robot = robots[0]
        for component in robot.get_components_by_class(unreal.SceneComponent):
            tags = {str(tag) for tag in component.get_editor_property("component_tags")}
            if isinstance(component, unreal.PoseableMeshComponent) and "LB.MR01.ArmPoseable" in tags:
                arm = component
            elif component.get_name().startswith("RP01_CollisionRoot"):
                collision = component
            elif component.get_name().startswith("SCK_ArmParkingCradle"):
                cradle = component
        if arm is None or collision is None or cradle is None:
            finish("FAIL__RUNTIME_PRESENTATION_CONTRACT_MISSING__NOT_PROMOTED")
            return
        collision_origin, collision_extent, _ = unreal.SystemLibrary.get_component_bounds(collision)
        collision_min = collision_origin - collision_extent
        collision_max = collision_origin + collision_extent
        cradle_world = cradle.get_world_location()

    # Measure the pose applied on the previous frame.
    if pending_pose is not None:
        origin, extent, _ = unreal.SystemLibrary.get_component_bounds(arm)
        arm_min = origin - extent
        arm_max = origin + extent
        overflow_x = max(0.0, collision_min.x - arm_min.x) + max(0.0, arm_max.x - collision_max.x)
        overflow_y = max(0.0, collision_min.y - arm_min.y) + max(0.0, arm_max.y - collision_max.y)
        tcp_world = arm.get_socket_location(unreal.Name("tcp"))
        tcp_distance = (tcp_world - cradle_world).length()
        size = extent * 2.0
        below_floor = max(0.0, -arm_min.z)
        # Primary: fit within travel footprint. Secondary: cradle proximity and
        # a compact but visibly articulated upright silhouette.
        score = ((overflow_x + overflow_y) * 20.0 + tcp_distance
                 + max(0.0, 65.0 - size.z) * 1.5 + below_floor * 40.0)
        rows.append({
            "joint_command_deg": pending_pose,
            "score": round(score, 4),
            "arm_bounds_origin_cm": vec(origin),
            "arm_bounds_size_cm": vec(size),
            "arm_bounds_min_cm": vec(arm_min),
            "arm_bounds_max_cm": vec(arm_max),
            "xy_overflow_beyond_collision_cm": [round(overflow_x, 4), round(overflow_y, 4)],
            "tcp_world_cm": vec(tcp_world),
            "cradle_distance_cm": round(tcp_distance, 4),
        })
        pending_pose = None

    if next_index >= len(poses):
        finish("PASS__FRAME_STEPPED_NATIVE_POSE_SEARCH_COMPLETE__VISUAL_REVIEW_REQUIRED__NOT_PROMOTED" if restore_failures == 0 else "FAIL__FRAME_STEPPED_NATIVE_POSE_SEARCH_INCOMPLETE__NOT_PROMOTED")
        return
    pose = poses[next_index]
    next_index += 1
    state = robot.capture_save_state()
    common = state.common
    common.unit_id = unreal.Name("MR01-POSE-SEARCH")
    common.variant_id = unreal.Name("LB-MR01")
    state.common = common
    state.arm_joint_degrees = pose
    state.arm_lift_millimetres = 0.0
    state.arm_parked = False
    if not robot.restore_save_state(state):
        restore_failures += 1
        return
    pending_pose = pose


handle = unreal.register_slate_post_tick_callback(tick)
