"""Read-only MR01 service-pose fit inspection against isolated dock map v008."""

from datetime import datetime, timezone
import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Developer/Validation/LB_ServiceDockActualRobotFit_v008"
OUT = ROOT / "Saved/Audits/SupportRobots/service_dock_mr01_stowed_fit_v009.json"
ACTORS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def tagged(actor, cls, tag):
    for item in actor.get_components_by_class(cls):
        if unreal.Name(tag) in item.get_editor_property("component_tags"):
            return item
    return None


def pose_arm(actor, lift_mm, joint_degrees):
    arm = tagged(actor, unreal.PoseableMeshComponent, "LB.MR01.ArmPoseable")
    if arm is None:
        raise RuntimeError("MR01 has no poseable arm")
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
    posed = {"root": refs["root"]}
    lift = unreal.Transform(
        refs["lift"].translation + unreal.Vector(0.0, 0.0, lift_mm / 10.0),
        refs["lift"].rotation.rotator(),
        refs["lift"].scale3d,
    )
    posed["lift"] = lift
    arm.set_bone_transform_by_name(unreal.Name("lift"), lift, unreal.BoneSpaces.COMPONENT_SPACE)
    commands = [
        ("j1_base", "lift", unreal.Rotator(0.0, joint_degrees[0] - 180.0, 0.0)),
        ("j2_shoulder", "j1_base", unreal.Rotator(joint_degrees[1], 0.0, 0.0)),
        ("j3_elbow", "j2_shoulder", unreal.Rotator(joint_degrees[2], 0.0, 0.0)),
        ("j4_wrist_roll", "j3_elbow", unreal.Rotator(0.0, 0.0, joint_degrees[3])),
        ("j5_wrist_pitch", "j4_wrist_roll", unreal.Rotator(joint_degrees[4], 0.0, 0.0)),
        ("j6_tool_roll", "j5_wrist_pitch", unreal.Rotator(0.0, 0.0, joint_degrees[5])),
        ("tool_coupler", "j6_tool_roll", unreal.Rotator()),
        ("tcp", "tool_coupler", unreal.Rotator()),
    ]
    for name, parent, delta in commands:
        local = unreal.MathLibrary.make_relative_transform(refs[name], refs[parent])
        local.rotation = unreal.MathLibrary.multiply_quat_quat(delta.quaternion(), local.rotation)
        value = unreal.MathLibrary.compose_transforms(local, posed[parent])
        posed[name] = value
        arm.set_bone_transform_by_name(unreal.Name(name), value, unreal.BoneSpaces.COMPONENT_SPACE)
    return arm


world = unreal.EditorLevelLibrary.get_editor_world()
current = world.get_outermost().get_name() if world is not None else ""
if current != MAP:
    raise RuntimeError("One-map rule violation: opened {}, expected {}".format(current, MAP))
mr = {actor.get_actor_label(): actor for actor in ACTORS.get_all_level_actors()}.get(
    "LB_DOCK_FIT_MR01_v021_ActualAuthority"
)
if mr is None:
    raise RuntimeError("Docked MR01 authority missing")

before_origin, before_extent = mr.get_actor_bounds(False)
stowed_pose = [180.0, -35.0, 130.0, 0.0, -95.0, 0.0]
arm = pose_arm(mr, 0.0, stowed_pose)
after_origin, after_extent = mr.get_actor_bounds(False)
before_size = before_extent * 2.0
after_size = after_extent * 2.0
payload = {
    "$schema": "cairnwell/audit/service-dock-mr01-stowed-fit-v009/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": (
        "PASS__STOWED_AGGREGATE_BOUNDS_FIT_126CM_PORTAL__READ_ONLY__NOT_PROMOTED"
        if after_size.x <= 126.0
        else "HOLD__STOWED_AGGREGATE_BOUNDS_STILL_EXCEED_126CM_PORTAL__READ_ONLY__NOT_PROMOTED"
    ),
    "source_map_loaded_not_saved": MAP,
    "actor": mr.get_actor_label(),
    "stowed_joint_pose_deg": stowed_pose,
    "before_bounds_size_cm": [round(before_size.x, 4), round(before_size.y, 4), round(before_size.z, 4)],
    "after_bounds_size_cm": [round(after_size.x, 4), round(after_size.y, 4), round(after_size.z, 4)],
    "portal_width_cm": 126.0,
    "stowed_lateral_clearance_cm": round(126.0 - after_size.x, 4),
    "map_saved": False,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
unreal.log("LINE_BOSS_MR01_STOWED_DOCK_FIT_V009 {}".format(payload["status"]))
