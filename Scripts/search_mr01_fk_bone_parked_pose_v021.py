"""Native MR01 parked-pose search using live FK bone centres, not fixed bounds.

The skeletal asset intentionally retains fixed component bounds, so articulated
fit is evaluated from the ten live bone transforms plus conservative link/joint
radii. The isolated PIE world is discarded and no map or asset is saved.
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
OUT = ROOT / "Saved/Audits/SupportRobots/mr01_fk_bone_parked_pose_search_v021.json"
BONES = ("j2_shoulder", "j3_elbow", "j4_wrist_roll", "j5_wrist_pitch",
         "j6_tool_roll", "tool_coupler", "tcp")
OUT.parent.mkdir(parents=True, exist_ok=True)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
unreal.EditorLevelLibrary.editor_play_simulate()
started = time.monotonic()
handle = None


def vec(value):
    return [round(float(value.x), 4), round(float(value.y), 4), round(float(value.z), 4)]


def finish(payload):
    global handle
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    unreal.log("LINE_BOSS_MR01_FK_BONE_POSE_V021 {} candidates={}".format(payload["status"], payload.get("candidate_count", 0)))
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
        finish({"$schema": "cairnwell/audit/mr01-fk-bone-parked-pose-search-v021/v1",
                "status": "FAIL__RUNTIME_CONTRACT_MISSING__NOT_PROMOTED",
                "map_saved": False, "promotion_authorized": False})
        return
    collision_origin, collision_extent, _ = unreal.SystemLibrary.get_component_bounds(collision)
    collision_min = collision_origin - collision_extent
    collision_max = collision_origin + collision_extent
    cradle_world = cradle.get_world_location()
    rows = []
    failures = 0
    for j1 in (180, 150, 120, 90, 60, 30, 0, -30, -60, -90, -120, -150):
        for j2 in (-95, -75, -55, -35, -15, 5, 25, 45, 65, 85, 105):
            for j3 in (-145, -120, -95, -70, -45, -20, 5, 30, 55, 80, 105, 130, 150):
                for j5 in (-120, -90, -60, -30, 0, 30, 60, 90, 120):
                    pose = [float(j1), float(j2), float(j3), 0.0, float(j5), 0.0]
                    state = robot.capture_save_state()
                    common = state.common
                    common.unit_id = unreal.Name("MR01-POSE-SEARCH")
                    common.variant_id = unreal.Name("LB-MR01")
                    state.common = common
                    state.arm_joint_degrees = pose
                    state.arm_lift_millimetres = 0.0
                    state.arm_parked = False
                    if not robot.restore_save_state(state):
                        failures += 1
                        continue
                    points = {
                        name: arm.get_bone_transform_by_name(
                            unreal.Name(name), unreal.BoneSpaces.WORLD_SPACE).translation
                        for name in BONES
                    }
                    xs = [point.x for point in points.values()]
                    ys = [point.y for point in points.values()]
                    zs = [point.z for point in points.values()]
                    # Conservative 16 cm radius around the articulated links.
                    radius = 16.0
                    min_x, max_x = min(xs) - radius, max(xs) + radius
                    min_y, max_y = min(ys) - radius, max(ys) + radius
                    min_z, max_z = min(zs) - radius, max(zs) + radius
                    overflow_x = max(0.0, collision_min.x - min_x) + max(0.0, max_x - collision_max.x)
                    overflow_y = max(0.0, collision_min.y - min_y) + max(0.0, max_y - collision_max.y)
                    tcp_distance = (points["tcp"] - cradle_world).length()
                    # Travel state should remain below the dock portal lintel and
                    # above the deck while keeping the TCP near its proved cradle.
                    high_penalty = max(0.0, max_z - 168.0)
                    low_penalty = max(0.0, 68.0 - min_z)
                    span_x = max_x - min_x
                    span_y = max_y - min_y
                    span_z = max_z - min_z
                    score = ((overflow_x + overflow_y) * 30.0 + tcp_distance * 4.0
                             + high_penalty * 25.0 + low_penalty * 25.0
                             + span_x * 0.5 + span_y * 0.5 + span_z * 0.25)
                    rows.append({
                        "joint_command_deg": pose,
                        "score": round(score, 4),
                        "conservative_link_envelope_min_cm": [round(min_x, 4), round(min_y, 4), round(min_z, 4)],
                        "conservative_link_envelope_max_cm": [round(max_x, 4), round(max_y, 4), round(max_z, 4)],
                        "conservative_link_envelope_size_cm": [round(span_x, 4), round(span_y, 4), round(span_z, 4)],
                        "xy_overflow_beyond_collision_cm": [round(overflow_x, 4), round(overflow_y, 4)],
                        "tcp_world_cm": vec(points["tcp"]),
                        "cradle_distance_cm": round(tcp_distance, 4),
                        "bone_centres_world_cm": {name: vec(point) for name, point in points.items()},
                    })
    rows.sort(key=lambda row: row["score"])
    finish({
        "$schema": "cairnwell/audit/mr01-fk-bone-parked-pose-search-v021/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS__LIVE_FK_BONE_SEARCH_COMPLETE__VISUAL_REVIEW_REQUIRED__NOT_PROMOTED" if rows and failures == 0 else "FAIL__LIVE_FK_BONE_SEARCH_INCOMPLETE__NOT_PROMOTED",
        "source_map_played_not_saved": MAP,
        "actor": ACTOR_LABEL,
        "candidate_count": len(rows),
        "restore_failures": failures,
        "collision_bounds_origin_cm": vec(collision_origin),
        "collision_bounds_size_cm": vec(collision_extent * 2.0),
        "parking_cradle_world_cm": vec(cradle_world),
        "assumed_conservative_link_radius_cm": 16.0,
        "dock_portal_lintel_working_limit_cm": 168.0,
        "best_candidates": rows[:100],
        "map_saved": False,
        "promotion_authorized": False,
    })


handle = unreal.register_slate_post_tick_callback(tick)
