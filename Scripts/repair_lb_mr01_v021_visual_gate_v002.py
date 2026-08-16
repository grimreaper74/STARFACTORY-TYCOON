"""Repair v021 wheel finishes, arm proof poses and isolated review staging."""

from datetime import datetime, timezone
import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Developer/Validation/LB_MR01_Candidate_v021_FunctionalAuthority"
BP_PATH = "/Game/LineBoss/Robots/Maintenance/MR01/Candidate_v021/Blueprints/BP_LB_MR01_MaintenanceAMR_v021"
MATERIAL_ROOT = "/Game/LineBoss/Robots/Shared/RP01/Candidate_v001/Materials"
AUDIT = ROOT / "Saved/Audits/lb_mr01_candidate_v021_visual_gate_repair_v002.json"

assets = unreal.EditorAssetLibrary
blueprints = unreal.BlueprintEditorLibrary
subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
data_library = unreal.SubobjectDataBlueprintFunctionLibrary
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)


def require(path, cls=None):
    asset = assets.load_asset(path)
    if asset is None or (cls is not None and not isinstance(asset, cls)):
        raise RuntimeError(f"Missing required asset {path}")
    return asset


def component_with_tag(actor, cls, tag):
    for component in actor.get_components_by_class(cls):
        if unreal.Name(tag) in component.get_editor_property("component_tags"):
            return component
    return None


def pose_arm(actor, lift_mm, joint_degrees):
    arm = component_with_tag(actor, unreal.PoseableMeshComponent, "LB.MR01.ArmPoseable")
    if arm is None:
        raise RuntimeError(f"{actor.get_actor_label()} has no poseable arm")
    names = ["root", "lift", "j1_base", "j2_shoulder", "j3_elbow", "j4_wrist_roll",
             "j5_wrist_pitch", "j6_tool_roll", "tool_coupler", "tcp"]
    for name in names:
        arm.reset_bone_transform_by_name(unreal.Name(name))
    refs = {name: arm.get_bone_transform_by_name(unreal.Name(name), unreal.BoneSpaces.COMPONENT_SPACE) for name in names}
    posed = {"root": refs["root"]}
    arm.set_bone_transform_by_name(unreal.Name("root"), posed["root"], unreal.BoneSpaces.COMPONENT_SPACE)
    lift = unreal.Transform(refs["lift"].translation + unreal.Vector(0.0, 0.0, lift_mm / 10.0),
                            refs["lift"].rotation.rotator(), refs["lift"].scale3d)
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
        component_transform = unreal.MathLibrary.compose_transforms(local, posed[parent])
        posed[name] = component_transform
        arm.set_bone_transform_by_name(unreal.Name(name), component_transform, unreal.BoneSpaces.COMPONENT_SPACE)
    return arm, posed


world = unreal.EditorLevelLibrary.get_editor_world()
if world is None or world.get_outermost().get_name() != MAP:
    raise RuntimeError(f"Open {MAP} before running visual repair")

# Correct the reusable Blueprint, not merely the proof map.
bp = require(BP_PATH, unreal.Blueprint)
materials = {
    "Wheel": require(f"{MATERIAL_ROOT}/M_LB_RP01_RubberBlack", unreal.MaterialInterface),
    "Rim": require(f"{MATERIAL_ROOT}/M_LB_RP01_SafetyYellow", unreal.MaterialInterface),
    "Hub": require(f"{MATERIAL_ROOT}/M_LB_RP01_FrameAnthracite", unreal.MaterialInterface),
    "Bearing": require(f"{MATERIAL_ROOT}/M_LB_RP01_BrushedSteel", unreal.MaterialInterface),
}
wheel_bindings = []
for handle in subsystem.k2_gather_subobject_data_for_blueprint(bp):
    data = subsystem.k2_find_subobject_data_from_handle(handle)
    component = data_library.get_object_for_blueprint(data, bp) or data_library.get_object(data)
    if not isinstance(component, unreal.StaticMeshComponent):
        continue
    tags = {str(tag) for tag in component.get_editor_property("component_tags")}
    for role, material in materials.items():
        if f"LB.MR01.WheelRole.{role}" in tags:
            component.set_material(0, material)
            wheel_bindings.append({"component": component.get_name(), "role": role, "material": material.get_path_name()})
            break
if len(wheel_bindings) != 16:
    raise RuntimeError(f"Expected sixteen wheel material bindings, found {len(wheel_bindings)}")
blueprints.compile_blueprint(bp)
if not assets.save_loaded_asset(bp, only_if_is_dirty=False):
    raise RuntimeError("Could not persist MR01 v021 wheel material repair")

by_label = {actor.get_actor_label(): actor for actor in actors.get_all_level_actors()}
stowed = by_label.get("LB_MR01_v021_Stowed_Authority")
reach = by_label.get("LB_MR01_v021_T6_MachineReach_Authority")
if stowed is None or reach is None:
    raise RuntimeError("Validation MR01 instances are missing")

pose_arm(stowed, 0.0, [180.0, -35.0, 130.0, 0.0, -95.0, 0.0])
reach_arm, reach_pose = pose_arm(reach, 400.0, [170.0, 0.0, 0.0, 0.0, 0.0, 0.0])
for actor, sleeve_z, carriage_z in ((stowed, 0.0, 0.0), (reach, 20.0, 40.0)):
    component_with_tag(actor, unreal.StaticMeshComponent, "LB.MR01.ArmLiftSleeve").set_editor_property("relative_location", unreal.Vector(0.0, 0.0, sleeve_z))
    component_with_tag(actor, unreal.StaticMeshComponent, "LB.MR01.ArmLiftCarriage").set_editor_property("relative_location", unreal.Vector(0.0, 0.0, carriage_z))

for index in range(1, 9):
    stored = component_with_tag(reach, unreal.StaticMeshComponent, f"LB.MR01.Tool.T{index}.Stored")
    equipped = component_with_tag(reach, unreal.StaticMeshComponent, f"LB.MR01.Tool.T{index}.Equipped")
    stored.set_visibility(index != 6, True)
    stored.set_hidden_in_game(index == 6, True)
    equipped.set_visibility(index == 6, True)
    equipped.set_hidden_in_game(index != 6, True)
equipped_t6 = component_with_tag(reach, unreal.StaticMeshComponent, "LB.MR01.Tool.T6.Equipped")
equipped_t6.attach_to_component(
    reach_arm, unreal.Name("tool_coupler"), unreal.AttachmentRule.SNAP_TO_TARGET,
    unreal.AttachmentRule.SNAP_TO_TARGET, unreal.AttachmentRule.KEEP_RELATIVE, False)

# Make the neutral stage large enough that no camera sees its outer edge.
floor = by_label.get("LB_MR01_v021_ValidationFloor")
backdrop = by_label.get("LB_MR01_v021_ValidationBackdrop")
if floor:
    floor.set_actor_scale3d(unreal.Vector(14.0, 20.0, 0.10))
if backdrop:
    backdrop.set_actor_scale3d(unreal.Vector(0.10, 20.0, 4.0))

if not levels.save_current_level():
    raise RuntimeError("Could not save repaired MR01 v021 validation map")
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps({
    "$schema": "line-boss/audit/lb-mr01-candidate-v021-visual-gate-repair-v002",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "WHEEL_FINISH_AND_PROOF_POSE_REPAIRED__FRESH_SCREENSHOTS_REQUIRED__NOT_PROMOTED",
    "blueprint": BP_PATH,
    "map": MAP,
    "wheel_material_bindings": wheel_bindings,
    "stowed_pose": {"lift_mm": 0.0, "joints_deg": [180.0, -35.0, 130.0, 0.0, -95.0, 0.0]},
    "reach_pose": {"lift_mm": 400.0, "joints_deg": [170.0, 0.0, 0.0, 0.0, 0.0, 0.0], "tool": "T6"},
    "promotion_authorized": False,
}, indent=2) + "\n", encoding="utf-8")
unreal.log(f"LB_MR01_V021_VISUAL_REPAIR_PASS wheel_bindings={len(wheel_bindings)}")
