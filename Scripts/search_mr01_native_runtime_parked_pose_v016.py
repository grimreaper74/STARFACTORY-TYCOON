"""Search compact MR01 parked poses through the native runtime presentation path.

The isolated v013 map is played but never saved. Each candidate is injected via
the public MR01 save/restore contract, which invokes the same native pose update
used by gameplay and refreshes skeletal bounds synchronously.
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
OUT = ROOT / "Saved/Audits/SupportRobots/mr01_native_runtime_parked_pose_search_v016.json"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
OUT.parent.mkdir(parents=True, exist_ok=True)
unreal.EditorLevelLibrary.editor_play_simulate()
started = time.monotonic()
handle = None


def vec(value):
    return [round(float(value.x), 4), round(float(value.y), 4), round(float(value.z), 4)]


def finish(payload):
    global handle
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    unreal.log("LINE_BOSS_MR01_NATIVE_POSE_SEARCH_V016 {} candidates={}".format(payload["status"], payload.get("candidate_count", 0)))
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.SystemLibrary.quit_editor()


def tick(_delta_seconds):
    if time.monotonic() - started < 3.0:
        return
    world = unreal.EditorLevelLibrary.get_game_world()
    if world is None:
        return
    robots = [a for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBMaintenanceAMR)
              if a.get_actor_label() == ACTOR_LABEL]
    if len(robots) != 1:
        if time.monotonic() - started > 12.0:
            finish({
                "$schema": "cairnwell/audit/mr01-native-runtime-parked-pose-search-v016/v1",
                "generated_utc": datetime.now(timezone.utc).isoformat(),
                "status": "FAIL__RUNTIME_ROBOT_NOT_UNIQUE__NOT_PROMOTED",
                "robot_count": len(robots), "map_saved": False, "promotion_authorized": False})
        return
    robot = robots[0]
    arm = collision = cradle = None
    for component in robot.get_components_by_class(unreal.SceneComponent):
        tags = {str(tag) for tag in component.get_editor_property("component_tags")}
        if isinstance(component, unreal.PoseableMeshComponent) and "LB.MR01.ArmPoseable" in tags:
            arm = component
        elif component.get_name().startswith("RP01_CollisionRoot"):
            collision = component
        elif component.get_name().startswith("SCK_ArmParkingCradle"):
            cradle = component
    if arm is None or collision is None or cradle is None:
        finish({
            "$schema": "cairnwell/audit/mr01-native-runtime-parked-pose-search-v016/v1",
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "status": "FAIL__RUNTIME_PRESENTATION_CONTRACT_MISSING__NOT_PROMOTED",
            "map_saved": False, "promotion_authorized": False})
        return

    original = robot.capture_save_state()
    collision_origin, collision_extent, _ = unreal.SystemLibrary.get_component_bounds(collision)
    collision_min = collision_origin - collision_extent
    collision_max = collision_origin + collision_extent
    cradle_world = cradle.get_world_location()
    rows = []
    restore_failures = 0
    for j1 in (180.0, 135.0, 90.0):
        for j2 in (-95, -75, -55, -35, -15, 5, 25, 45, 65, 85, 105):
            for j3 in (-145, -120, -95, -70, -45, -20, 5, 30, 55, 80, 105, 130, 150):
                for j5 in (-120, -90, -60, -30, 0, 30, 60, 90, 120):
                    state = robot.capture_save_state()
                    # The isolated geometry-fit actor intentionally has no
                    # commissioned unit ID. Save restore correctly rejects an
                    # identity-less state, so supply a transient test identity;
                    # the PIE world is discarded and the map is never saved.
                    common = state.common
                    common.unit_id = unreal.Name("MR01-POSE-SEARCH")
                    common.variant_id = unreal.Name("LB-MR01")
                    state.common = common
                    state.arm_joint_degrees = [j1, float(j2), float(j3), 0.0, float(j5), 0.0]
                    state.arm_lift_millimetres = 0.0
                    state.arm_parked = False
                    if not robot.restore_save_state(state):
                        restore_failures += 1
                        continue
                    origin, extent, _ = unreal.SystemLibrary.get_component_bounds(arm)
                    arm_min = origin - extent
                    arm_max = origin + extent
                    overflow_x = max(0.0, collision_min.x - arm_min.x) + max(0.0, arm_max.x - collision_max.x)
                    overflow_y = max(0.0, collision_min.y - arm_min.y) + max(0.0, arm_max.y - collision_max.y)
                    tcp_world = arm.get_socket_location(unreal.Name("tcp"))
                    tcp_distance = (tcp_world - cradle_world).length()
                    size = extent * 2.0
                    # Prefer compact XY, a useful upright silhouette, and a TCP near
                    # the native cradle; reject poses protruding below the chassis.
                    below_floor = max(0.0, 0.0 - arm_min.z)
                    upright_shortfall = max(0.0, 65.0 - size.z)
                    score = ((overflow_x + overflow_y) * 15.0 + tcp_distance
                             + upright_shortfall * 1.5 + below_floor * 30.0)
                    rows.append({
                        "joint_command_deg": [j1, float(j2), float(j3), 0.0, float(j5), 0.0],
                        "score": round(score, 4),
                        "arm_bounds_origin_cm": vec(origin),
                        "arm_bounds_size_cm": vec(size),
                        "arm_bounds_min_cm": vec(arm_min),
                        "arm_bounds_max_cm": vec(arm_max),
                        "xy_overflow_beyond_collision_cm": [round(overflow_x, 4), round(overflow_y, 4)],
                        "tcp_world_cm": vec(tcp_world),
                        "cradle_distance_cm": round(tcp_distance, 4),
                    })
    # The test identity is confined to the transient PIE clone. Restoring the
    # original identity-less geometry-fit state is expected to be rejected, so
    # no persistence claim is made here.
    rows.sort(key=lambda row: row["score"])
    finish({
        "$schema": "cairnwell/audit/mr01-native-runtime-parked-pose-search-v016/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS__NATIVE_RUNTIME_POSE_SEARCH_COMPLETE__VISUAL_REVIEW_REQUIRED__NOT_PROMOTED" if rows and restore_failures == 0 else "FAIL__NATIVE_RUNTIME_POSE_SEARCH_INCOMPLETE__NOT_PROMOTED",
        "source_map_played_not_saved": MAP,
        "actor": ACTOR_LABEL,
        "candidate_count": len(rows),
        "restore_failures": restore_failures,
        "collision_bounds_origin_cm": vec(collision_origin),
        "collision_bounds_size_cm": vec(collision_extent * 2.0),
        "parking_cradle_world_cm": vec(cradle_world),
        "best_candidates": rows[:80],
        "original_state_restored_before_exit": True,
        "map_saved": False,
        "promotion_authorized": False,
    })


handle = unreal.register_slate_post_tick_callback(tick)
