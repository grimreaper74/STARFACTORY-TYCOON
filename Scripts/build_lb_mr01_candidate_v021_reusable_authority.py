"""Build reusable MR01 v021 on native authority with v020 connected-lift art."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re

import unreal

ROOT = Path(unreal.Paths.project_dir())
SOURCE_ROOT = "/Game/LineBoss/Robots/Maintenance/MR01/Candidate_v020"
PAYLOAD_ROOT = SOURCE_ROOT + "/Payload"
ARM_ROOT = SOURCE_ROOT + "/Arm"
TOOLS_ROOT = SOURCE_ROOT + "/Tools"
RP01_ROOT = "/Game/LineBoss/Robots/Shared/RP01/Candidate_v001/Meshes"
CANDIDATE_ROOT = "/Game/LineBoss/Robots/Maintenance/MR01/Candidate_v021"
BP_PATH = CANDIDATE_ROOT + "/Blueprints/BP_LB_MR01_MaintenanceAMR_v021"
AUDIT = ROOT / "Saved/Audits/lb_mr01_candidate_v021_reusable_authority_build.json"

assets = unreal.EditorAssetLibrary
blueprints = unreal.BlueprintEditorLibrary
subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
data_library = unreal.SubobjectDataBlueprintFunctionLibrary


def require(path, cls=None):
    asset = assets.load_asset(path)
    if asset is None or (cls is not None and not isinstance(asset, cls)):
        raise RuntimeError(f"Missing or wrong-class asset {path}")
    return asset


def gather_handles(blueprint):
    result = {}
    objects = {}
    for handle in subsystem.k2_gather_subobject_data_for_blueprint(blueprint):
        data = subsystem.k2_find_subobject_data_from_handle(handle)
        name = str(data_library.get_variable_name(data))
        obj = data_library.get_object_for_blueprint(data, blueprint) or data_library.get_object(data)
        # Native inherited scene components do not necessarily expose a Blueprint
        # variable name through SubobjectData. Their template object names still
        # carry the exact C++ contract names and are valid attachment handles.
        if (not name or name == "None") and obj is not None:
            name = obj.get_name()
        if name and name != "None" and name not in result:
            result[name] = handle
            objects[name] = obj
    return result, objects


def add_component(blueprint, parent_handle, component_class, name):
    result = subsystem.add_new_subobject(params=unreal.AddNewSubobjectParams(
        parent_handle=parent_handle,
        new_class=component_class,
        blueprint_context=blueprint,
        conform_transform_to_parent=False,
        skip_mark_blueprint_modified=False,
    ))
    handle = result[0]
    if not data_library.is_handle_valid(handle):
        raise RuntimeError(f"Could not add {name}: {result[1] if len(result) > 1 else ''}")
    subsystem.rename_subobject(handle=handle, new_name=unreal.Text(name))
    data = subsystem.k2_find_subobject_data_from_handle(handle)
    component = data_library.get_object_for_blueprint(data, blueprint) or data_library.get_object(data)
    if component is None:
        raise RuntimeError(f"Could not resolve component template {name}")
    return handle, component


def safe_name(value):
    value = value.replace("+", "Pos").replace("-", "Neg")
    value = re.sub(r"[^A-Za-z0-9_]", "_", value)
    return value[:100]


def configure_scene(component, location=(0.0, 0.0, 0.0), rotation=(0.0, 0.0, 0.0), tags=()):
    component.set_editor_property("relative_location", unreal.Vector(*location))
    component.set_editor_property("relative_rotation", unreal.Rotator(*rotation))
    component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
    component.set_editor_property("component_tags", [unreal.Name(tag) for tag in tags])


def configure_static(component, mesh, location=(0.0, 0.0, 0.0), rotation=(0.0, 0.0, 0.0), tags=(), visible=True):
    component.set_static_mesh(mesh)
    configure_scene(component, location, rotation, tags)
    component.set_collision_profile_name(unreal.Name("NoCollision"))
    component.set_editor_property("visible", visible)
    component.set_editor_property("hidden_in_game", not visible)


if assets.does_directory_exist(CANDIDATE_ROOT):
    raise RuntimeError(f"Preserve existing candidate namespace {CANDIDATE_ROOT}")
import_audit = json.loads((ROOT / "Saved/Audits/lb_mr01_candidate_v020_unreal_import.json").read_text(encoding="utf-8"))
if import_audit.get("status") != "IMPORT_GATE_PASS__CANDIDATE_NOT_PROMOTED" or import_audit.get("asset_counts", {}).get("arm_bone_count") != 10:
    raise RuntimeError("v020 strict Unreal import authority is not green")

parent_class = unreal.load_class(None, "/Script/LineBossCarFactory.LBMaintenanceAMR")
if parent_class is None:
    raise RuntimeError("Native ALBMaintenanceAMR class is unavailable")
blueprint = blueprints.create_blueprint_asset_with_parent(BP_PATH, parent_class)
if not isinstance(blueprint, unreal.Blueprint):
    raise RuntimeError(f"Could not create {BP_PATH}")
handles, inherited = gather_handles(blueprint)
required_pivots = ["RobotVisualRoot"]
missing = [name for name in required_pivots if name not in handles]
if missing:
    raise RuntimeError(f"Native MR01 contract pivots missing: {missing}")

payload_paths = [path for path in assets.list_assets(PAYLOAD_ROOT, recursive=False, include_folder=False) if isinstance(assets.load_asset(path), unreal.StaticMesh)]
if len(payload_paths) != 345:
    raise RuntimeError(f"Expected 345 v020 payload meshes including connected sleeve, found {len(payload_paths)}")
payload_meshes = {assets.load_asset(path).get_name(): assets.load_asset(path) for path in payload_paths}

component_rows = []
moving_names = {"SM_LB_MR01_ArmLiftSleeveStage2_v020", "SM_LB_MR01_ArmLiftCarriage"}


def parent_contract_for_mesh(name):
    for corner in ("FL", "FR", "RL", "RR"):
        if f"_{corner}" in name and "Outrigger" in name:
            if "Foot" in name or ("Jack" in name and "JackBody" not in name):
                return f"PVT_Outrigger_{corner}_Drop"
            return f"PVT_Outrigger_{corner}_Extend"
    if any(token in name for token in ("SensorMast", "SensorHead", "MastWorkLight", "MastYoke", "MastSensor", "MastTopGuard", "MastLens")):
        return "PVT_MastLift"
    if name.startswith("SM_LB_MR01_PartsDrawer") or "PartsDrawerFront" in name:
        return "PVT_PartsDrawer"
    if "Door_L_" in name or "ForwardServiceDoor_L" in name:
        return "PVT_Door_Left"
    if "Door_R_" in name or "ForwardServiceDoor_R" in name:
        return "PVT_Door_Right"
    if name == "SM_LB_MR01_RearToolDoor":
        return "PVT_Door_Rear"
    return "RobotVisualRoot"


pivot_world = {
    "RobotVisualRoot": (0.0, 0.0, 0.0),
    "PVT_Outrigger_FL_Extend": (43.0, -43.0, 22.0), "PVT_Outrigger_FR_Extend": (43.0, 43.0, 22.0),
    "PVT_Outrigger_RL_Extend": (-43.0, -43.0, 22.0), "PVT_Outrigger_RR_Extend": (-43.0, 43.0, 22.0),
    "PVT_Outrigger_FL_Drop": (43.0, -43.0, 16.0), "PVT_Outrigger_FR_Drop": (43.0, 43.0, 16.0),
    "PVT_Outrigger_RL_Drop": (-43.0, -43.0, 16.0), "PVT_Outrigger_RR_Drop": (-43.0, 43.0, 16.0),
    "PVT_MastLift": (-45.0, 28.0, 85.0), "PVT_PartsDrawer": (-15.0, -43.0, 58.0),
    "PVT_Door_Left": (-10.0, -45.5, 70.0), "PVT_Door_Right": (-10.0, 45.5, 70.0),
    "PVT_Door_Rear": (-72.0, 0.0, 72.0),
}

for mesh_name in sorted(payload_meshes):
    mesh = payload_meshes[mesh_name]
    parent_name = "RobotVisualRoot" if mesh_name in moving_names else parent_contract_for_mesh(mesh_name)
    # Python's SubobjectData API does not expose C++-created inherited pivots.
    # Author the baked CFR-space visual beneath RobotVisualRoot, then let the
    # native authority reattach tagged groups to their runtime pivots with
    # KeepWorldTransform in BeginPlay.
    parent_handle = handles["RobotVisualRoot"]
    handle, component = add_component(blueprint, parent_handle, unreal.StaticMeshComponent, "Visual_" + safe_name(mesh_name))
    location = (0.0, 0.0, 0.0)
    tags = ["LB.MR01.Payload", "LB.Asset.Candidate.v020", "LB.Asset.CandidateNotPromoted"]
    if parent_name != "RobotVisualRoot":
        tags.append(f"LB.MR01.AttachTo.{parent_name}")
    if mesh_name == "SM_LB_MR01_ArmLiftSleeveStage2_v020":
        tags.append("LB.MR01.ArmLiftSleeve")
    elif mesh_name == "SM_LB_MR01_ArmLiftCarriage":
        tags.append("LB.MR01.ArmLiftCarriage")
    configure_static(component, mesh, location, tags=tags)
    component_rows.append({"component": component.get_name(), "mesh": mesh.get_path_name(), "parent": parent_name, "location_cm": location})

# One ten-bone poseable arm; the native authority applies component-space FK.
skeletal_paths = [path for path in assets.list_assets(ARM_ROOT, recursive=False, include_folder=False) if isinstance(assets.load_asset(path), unreal.SkeletalMesh)]
if len(skeletal_paths) != 1:
    raise RuntimeError(f"Expected one skeletal arm, found {skeletal_paths}")
arm_mesh = require(skeletal_paths[0], unreal.SkeletalMesh)
arm_handle, arm_component = add_component(blueprint, handles["RobotVisualRoot"], unreal.PoseableMeshComponent, "Visual_MR01_ArmPoseable")
arm_component.set_editor_property("skinned_asset", arm_mesh)
configure_scene(arm_component, tags=("LB.MR01.ArmPoseable", "LB.Asset.Candidate.v020", "LB.Asset.CandidateNotPromoted"))
arm_component.set_collision_profile_name(unreal.Name("NoCollision"))

# Exact four independently driven RP01 corner modules. Each visual references
# the shared RP01 mesh assets directly; no wheel/hub geometry is duplicated.
wheel_rows = []
wheel_positions = {"FL": (50.0, -40.5, 17.0), "FR": (50.0, 40.5, 17.0), "RL": (-50.0, -40.5, 17.0), "RR": (-50.0, 40.5, 17.0)}
for corner, side in (("FL", "L"), ("FR", "R"), ("RL", "L"), ("RR", "R")):
    parent = handles["RobotVisualRoot"]
    for role, asset_name in (
        ("Wheel", f"SM_LB_RP01_DriveWheel_{side}"),
        ("Rim", f"SM_LB_RP01_DriveRim_{side}"),
        ("Hub", f"SM_LB_RP01_DriveHubCap_{side}"),
        ("Bearing", f"SM_LB_RP01_DriveBearing_{side}"),
    ):
        mesh = require(f"{RP01_ROOT}/{asset_name}", unreal.StaticMesh)
        box = mesh.get_bounding_box()
        centre = (box.min + box.max) * 0.5
        corner_position = wheel_positions[corner]
        location = (corner_position[0] - centre.x, corner_position[1] - centre.y, corner_position[2] - centre.z)
        _handle, component = add_component(blueprint, parent, unreal.StaticMeshComponent, f"Visual_RP01_{role}_{corner}")
        configure_static(component, mesh, location, tags=(
            f"LB.MR01.WheelModule.{corner}", f"LB.MR01.WheelRole.{role}",
            f"LB.MR01.AttachTo.PVT_Wheel_{corner}", "LB.MR01.DriveIndependent",
            "LB.RP01.SharedGeometry", "LB.Asset.CandidateNotPromoted",
        ))
        wheel_rows.append({"corner": corner, "role": role, "mesh": mesh.get_path_name(), "relative_location_cm": list(location)})

# Carousel and mutually-exclusive stored/equipped tool visuals.
carousel = require(f"{TOOLS_ROOT}/SM_LB_MR01_ToolCarousel8_v013", unreal.StaticMesh)
_handle, carousel_component = add_component(blueprint, handles["RobotVisualRoot"], unreal.StaticMeshComponent, "Visual_MR01_ToolCarousel")
configure_static(carousel_component, carousel, tags=("LB.MR01.ToolCarousel", "LB.MR01.AttachTo.PVT_ToolCarousel", "LB.Asset.CandidateNotPromoted"))
tool_rows = []
for index in range(1, 9):
    mesh = require(f"{TOOLS_ROOT}/SM_LB_MR01_Tool_T{index}_v013", unreal.StaticMesh)
    _stored_handle, stored = add_component(blueprint, handles["RobotVisualRoot"], unreal.StaticMeshComponent, f"Visual_Tool_T{index}_Stored")
    configure_static(stored, mesh, tags=(f"LB.MR01.Tool.T{index}.Stored", f"LB.MR01.AttachTo.SCK_ToolRack_{index:02d}", "LB.Asset.CandidateNotPromoted"), visible=True)
    _equipped_handle, equipped = add_component(blueprint, arm_handle, unreal.StaticMeshComponent, f"Visual_Tool_T{index}_Equipped")
    configure_static(equipped, mesh, rotation=(0.0, 180.0, 0.0), tags=(f"LB.MR01.Tool.T{index}.Equipped", "LB.Asset.CandidateNotPromoted"), visible=False)
    try:
        attached = equipped.attach_to_component(
            arm_component, unreal.Name("tool_coupler"),
            unreal.AttachmentRule.KEEP_RELATIVE, unreal.AttachmentRule.KEEP_RELATIVE,
            unreal.AttachmentRule.KEEP_RELATIVE, False)
        if not attached:
            raise RuntimeError("attach_to_component returned false")
    except Exception as exc:
        raise RuntimeError(f"Could not attach equipped T{index} to tool_coupler: {exc}")
    tool_rows.append({"tool": f"T{index}", "stored_component": stored.get_name(), "equipped_component": equipped.get_name(), "mesh": mesh.get_path_name()})

blueprints.compile_blueprint(blueprint)
generated_class = blueprints.generated_class(blueprint)
if generated_class is None:
    raise RuntimeError("MR01 v021 generated class unavailable")
default_object = unreal.get_default_object(generated_class)
default_object.set_editor_property("tags", [
    unreal.Name("LB.SupportRobot.LB-MR01"), unreal.Name("LB.Asset.Candidate.v021"),
    unreal.Name("LB.Asset.CandidateNotPromoted"), unreal.Name("LB.Brand.CairnwellAutomotive"),
    unreal.Name("LB.Site.MoorcrossWorks"), unreal.Name("LB.MR01.FourIndependentCornerDriveModules"),
    unreal.Name("LB.MR01.ConnectedLift.v020"), unreal.Name("LB.MR01.NativeAuthority"),
])
blueprints.compile_blueprint(blueprint)
if not assets.save_loaded_asset(blueprint, only_if_is_dirty=False):
    raise RuntimeError(f"Could not save {BP_PATH}")

AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps({
    "$schema": "line-boss/audit/lb-mr01-candidate-v021-reusable-authority-build",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "REUSABLE_NATIVE_AUTHORITY_ASSEMBLY_BUILT__FRESH_RELOAD_RUNTIME_AND_CAMERA_GATES_REQUIRED__NOT_PROMOTED",
    "blueprint": BP_PATH,
    "parent_class": "/Script/LineBossCarFactory.LBMaintenanceAMR",
    "source_candidate": SOURCE_ROOT,
    "payload_component_count": len(component_rows),
    "poseable_arm_count": 1,
    "arm_bone_count": 10,
    "wheel_module_count": 4,
    "wheel_role_component_count": len(wheel_rows),
    "all_wheel_geometry_references_shared_rp01": all(row["mesh"].startswith(RP01_ROOT) for row in wheel_rows),
    "caster_wheels_added": 0,
    "tool_count": len(tool_rows),
    "stored_tool_visual_count": len(tool_rows),
    "equipped_tool_visual_count": len(tool_rows),
    "equipped_tools_default_visible": 0,
    "connected_lift_components": ["Visual_SM_LB_MR01_ArmLiftSleeveStage2_v020", "Visual_SM_LB_MR01_ArmLiftCarriage"],
    "native_authority_features": ["arm_fk", "two_stage_lift", "four_outriggers", "mast", "tool_identity", "save_restore", "work_permits"],
    "line_boss_diegetic_branding_added": False,
    "promotion_authorized": False,
    "remaining_gates": ["fresh reload", "runtime arm/lift/tool proof", "collision and navigation", "save-state", "fixed-camera Unreal visual review"],
    "components": component_rows,
    "wheel_components": wheel_rows,
    "tool_components": tool_rows,
}, indent=2) + "\n", encoding="utf-8")
unreal.log(f"LB_MR01_V021_REUSABLE_BUILD_PASS payload={len(component_rows)} wheel_modules=4 tools=8 bp={BP_PATH}")
