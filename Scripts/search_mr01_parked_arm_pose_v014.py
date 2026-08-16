"""Read-only coarse search for a compact upright MR01 parked-arm pose.

The v013 validation map is loaded but never saved. Candidate poses are applied only
to the poseable presentation component; native authority data is not edited.
"""

from datetime import datetime, timezone
import json
import math
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Developer/Validation/LB_ServiceDockActualRobotFit_v013"
ACTOR_LABEL = "LB_DOCK_FIT_MR01_v022_ActualAuthority"
OUT = ROOT / "Saved/Audits/SupportRobots/mr01_parked_arm_pose_search_v014.json"
ACTORS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def vec(value):
    return [round(float(value.x), 4), round(float(value.y), 4), round(float(value.z), 4)]


world = unreal.EditorLevelLibrary.get_editor_world()
current = world.get_outermost().get_name() if world is not None else ""
if current != MAP:
    raise RuntimeError("One-map rule violation: opened {}, expected {}".format(current, MAP))
actor = {item.get_actor_label(): item for item in ACTORS.get_all_level_actors()}.get(ACTOR_LABEL)
if actor is None:
    raise RuntimeError("Missing {}".format(ACTOR_LABEL))

arm = None
cradle = None
collision = None
for component in actor.get_components_by_class(unreal.SceneComponent):
    if isinstance(component, unreal.PoseableMeshComponent) and unreal.Name("LB.MR01.ArmPoseable") in component.get_editor_property("component_tags"):
        arm = component
    elif component.get_name() == "SCK_ArmParkingCradle":
        cradle = component
    elif component.get_name() == "RP01_CollisionRoot":
        collision = component
if arm is None or cradle is None or collision is None:
    raise RuntimeError("Missing arm/cradle/collision authority")

names = [
    "root", "lift", "j1_base", "j2_shoulder", "j3_elbow", "j4_wrist_roll",
    "j5_wrist_pitch", "j6_tool_roll", "tool_coupler", "tcp",
]
for name in names:
    arm.reset_bone_transform_by_name(unreal.Name(name))
refs = {
    name: arm.get_bone_transform_by_name(unreal.Name(name), unreal.BoneSpaces.COMPONENT_SPACE)
    for name in names
}


def apply_pose(j2, j3, j5):
    posed = {"root": refs["root"], "lift": refs["lift"]}
    arm.set_bone_transform_by_name(unreal.Name("root"), refs["root"], unreal.BoneSpaces.COMPONENT_SPACE)
    arm.set_bone_transform_by_name(unreal.Name("lift"), refs["lift"], unreal.BoneSpaces.COMPONENT_SPACE)
    commands = [
        ("j1_base", "lift", unreal.Rotator(0.0, 0.0, 0.0)),
        ("j2_shoulder", "j1_base", unreal.Rotator(float(j2), 0.0, 0.0)),
        ("j3_elbow", "j2_shoulder", unreal.Rotator(float(j3), 0.0, 0.0)),
        ("j4_wrist_roll", "j3_elbow", unreal.Rotator()),
        ("j5_wrist_pitch", "j4_wrist_roll", unreal.Rotator(float(j5), 0.0, 0.0)),
        ("j6_tool_roll", "j5_wrist_pitch", unreal.Rotator()),
        ("tool_coupler", "j6_tool_roll", unreal.Rotator()),
        ("tcp", "tool_coupler", unreal.Rotator()),
    ]
    for name, parent, delta in commands:
        local = unreal.MathLibrary.make_relative_transform(refs[name], refs[parent])
        local.rotation = unreal.MathLibrary.multiply_quat_quat(delta.quaternion(), local.rotation)
        value = unreal.MathLibrary.compose_transforms(local, posed[parent])
        posed[name] = value
        arm.set_bone_transform_by_name(unreal.Name(name), value, unreal.BoneSpaces.COMPONENT_SPACE)
    # Python exposes SetBoneTransform but not RefreshBoneTransforms in UE 5.8;
    # each setter marks the poseable component dirty before the bounds query.


collision_origin, collision_extent, _ = unreal.SystemLibrary.get_component_bounds(collision)
cradle_world = cradle.get_world_location()
rows = []
for j2 in (-95, -75, -55, -35, -15, 5, 25, 45, 65, 85, 105):
    for j3 in (-145, -120, -95, -70, -45, -20, 5, 30, 55, 80, 105, 130, 150):
        for j5 in (-120, -90, -60, -30, 0, 30, 60, 90, 120):
            apply_pose(j2, j3, j5)
            origin, extent, _ = unreal.SystemLibrary.get_component_bounds(arm)
            arm_min = origin - extent
            arm_max = origin + extent
            collision_min = collision_origin - collision_extent
            collision_max = collision_origin + collision_extent
            overflow_x = max(0.0, collision_min.x - arm_min.x) + max(0.0, arm_max.x - collision_max.x)
            overflow_y = max(0.0, collision_min.y - arm_min.y) + max(0.0, arm_max.y - collision_max.y)
            try:
                tcp_world = arm.get_socket_location(unreal.Name("tcp"))
            except Exception:
                tcp_world = origin
            tcp_distance = (tcp_world - cradle_world).length()
            size = extent * 2.0
            upright_penalty = max(0.0, 55.0 - size.z)
            score = (overflow_x + overflow_y) * 12.0 + tcp_distance + upright_penalty * 0.75
            rows.append({
                "joint_command_deg": [180.0, float(j2), float(j3), 0.0, float(j5), 0.0],
                "score": round(score, 4),
                "arm_bounds_origin_cm": vec(origin),
                "arm_bounds_size_cm": vec(size),
                "xy_overflow_beyond_collision_cm": [round(overflow_x, 4), round(overflow_y, 4)],
                "tcp_world_cm": vec(tcp_world),
                "cradle_distance_cm": round(tcp_distance, 4),
            })

rows.sort(key=lambda row: row["score"])
payload = {
    "$schema": "cairnwell/audit/mr01-parked-arm-pose-search-v014/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__TRANSIENT_POSE_SEARCH_COMPLETE__VISUAL_REVIEW_REQUIRED__NO_ASSET_SAVED",
    "source_map_loaded_not_saved": MAP,
    "actor": ACTOR_LABEL,
    "candidate_count": len(rows),
    "collision_bounds_origin_cm": vec(collision_origin),
    "collision_bounds_size_cm": vec(collision_extent * 2.0),
    "parking_cradle_world_cm": vec(cradle_world),
    "best_candidates": rows[:40],
    "map_saved": False,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
unreal.log("LINE_BOSS_MR01_PARKED_ARM_SEARCH_V014 candidates={}".format(len(rows)))
