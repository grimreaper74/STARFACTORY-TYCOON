"""Fresh-process structural audit for reusable MR01 v021."""

from datetime import datetime, timezone
import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BP_PATH = "/Game/LineBoss/Robots/Maintenance/MR01/Candidate_v021/Blueprints/BP_LB_MR01_MaintenanceAMR_v021"
RP01_ROOT = "/Game/LineBoss/Robots/Shared/RP01/Candidate_v001/Meshes/"
V020_ROOT = "/Game/LineBoss/Robots/Maintenance/MR01/Candidate_v020/"
AUDIT = ROOT / "Saved/Audits/lb_mr01_candidate_v021_reusable_authority_fresh_audit.json"


def tags(component):
    return {str(tag) for tag in component.get_editor_property("component_tags")}


def mesh_path(component):
    mesh = component.get_editor_property("static_mesh")
    return mesh.get_path_name() if mesh is not None else ""


bp = unreal.EditorAssetLibrary.load_asset(BP_PATH)
if not isinstance(bp, unreal.Blueprint):
    raise RuntimeError(f"Fresh reload failed for {BP_PATH}")
generated_class = unreal.BlueprintEditorLibrary.generated_class(bp)
if generated_class is None:
    raise RuntimeError("Generated class is unavailable after fresh reload")
cdo = unreal.get_default_object(generated_class)
if cdo is None:
    raise RuntimeError("Generated-class default object is unavailable")
actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
instance = actor_subsystem.spawn_actor_from_class(generated_class, unreal.Vector(0.0, 0.0, -100000.0), unreal.Rotator())
if instance is None:
    raise RuntimeError("Could not spawn disposable fresh-audit instance")

static_components = instance.get_components_by_class(unreal.StaticMeshComponent)
poseable_components = instance.get_components_by_class(unreal.PoseableMeshComponent)
wheel_roles = {role: [] for role in ("Wheel", "Rim", "Hub", "Bearing")}
wheel_corners = {corner: [] for corner in ("FL", "FR", "RL", "RR")}
stored = []
equipped = []
attach_contracts = []
payload = []
working_title_hits = []

for component in static_components:
    component_tags = tags(component)
    path = mesh_path(component)
    if "LB.MR01.Payload" in component_tags:
        payload.append(component)
    for role in wheel_roles:
        if f"LB.MR01.WheelRole.{role}" in component_tags:
            wheel_roles[role].append(component)
    for corner in wheel_corners:
        if f"LB.MR01.WheelModule.{corner}" in component_tags:
            wheel_corners[corner].append(component)
    if any(tag.startswith("LB.MR01.Tool.T") and tag.endswith(".Stored") for tag in component_tags):
        stored.append(component)
    if any(tag.startswith("LB.MR01.Tool.T") and tag.endswith(".Equipped") for tag in component_tags):
        equipped.append(component)
    attach_contracts.extend(tag for tag in component_tags if tag.startswith("LB.MR01.AttachTo."))
    if "LineBoss" in component.get_name() or "LineBoss" in path.rsplit("/", 1)[-1]:
        working_title_hits.append(component.get_name())

arm_bones = []
arm_mesh_path = ""
if len(poseable_components) == 1:
    arm_asset = poseable_components[0].get_editor_property("skinned_asset")
    arm_mesh_path = arm_asset.get_path_name() if arm_asset is not None else ""
    if isinstance(arm_asset, unreal.SkeletalMesh):
        skeleton = arm_asset.get_editor_property("skeleton")
        if skeleton is not None:
            arm_bones = [str(name) for name in skeleton.get_reference_pose().get_bone_names()]

wheel_paths = [mesh_path(component) for role in wheel_roles.values() for component in role]
actor_tags = {str(tag) for tag in instance.get_editor_property("tags")}
checks = {
    "fresh_blueprint_reload": True,
    "native_parent_class": isinstance(cdo, unreal.LBMaintenanceAMR),
    "payload_exactly_345": len(payload) == 345,
    "one_poseable_arm": len(poseable_components) == 1,
    "arm_uses_v020_asset": arm_mesh_path.startswith(V020_ROOT),
    "arm_exactly_ten_authored_bones": len(arm_bones) == 10,
    "four_corner_modules_exact": all(len(components) == 4 for components in wheel_corners.values()),
    "wheel_role_counts_exact": all(len(components) == 4 for components in wheel_roles.values()),
    "all_wheel_geometry_is_shared_rp01": len(wheel_paths) == 16 and all(path.startswith(RP01_ROOT) for path in wheel_paths),
    "no_caster_geometry": not any("Caster" in path for path in wheel_paths),
    "eight_stored_tools": len(stored) == 8,
    "eight_equipped_tools": len(equipped) == 8,
    "stored_visible_by_default": all(component.get_editor_property("visible") and not component.get_editor_property("hidden_in_game") for component in stored),
    "equipped_hidden_by_default": all(not component.get_editor_property("visible") and component.get_editor_property("hidden_in_game") for component in equipped),
    "runtime_contract_attachment_tags_present": len(attach_contracts) >= 29,
    "connected_lift_tags_present": any("LB.MR01.ArmLiftSleeve" in tags(component) for component in payload) and any("LB.MR01.ArmLiftCarriage" in tags(component) for component in payload),
    "cairnwell_and_moorcross_identity_tags": {"LB.Brand.CairnwellAutomotive", "LB.Site.MoorcrossWorks"}.issubset(actor_tags),
    "working_title_absent_from_diegetic_assets": not working_title_hits,
}

result = {
    "$schema": "line-boss/audit/lb-mr01-candidate-v021-reusable-authority-fresh",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "FRESH_RELOAD_STRUCTURE_PASS__RUNTIME_AND_VISUAL_GATES_REQUIRED__NOT_PROMOTED" if all(checks.values()) else "FAIL",
    "blueprint": BP_PATH,
    "generated_class": generated_class.get_path_name(),
    "counts": {
        "static_components": len(static_components),
        "payload": len(payload),
        "poseable_arm": len(poseable_components),
        "arm_bones": len(arm_bones),
        "wheel_components": len(wheel_paths),
        "stored_tools": len(stored),
        "equipped_tools": len(equipped),
        "contract_attachment_tags": len(attach_contracts),
    },
    "arm_bone_names": arm_bones,
    "wheel_meshes": wheel_paths,
    "checks": checks,
    "promotion_authorized": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
actor_subsystem.destroy_actor(instance)
if result["status"] == "FAIL":
    raise RuntimeError({name: value for name, value in checks.items() if not value})
unreal.log(f"LB_MR01_V021_FRESH_AUDIT_PASS components={len(static_components)} bones={len(arm_bones)}")
