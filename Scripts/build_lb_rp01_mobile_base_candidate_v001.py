"""Build the first canonical-path RP01 mobile-base parent candidate.

The authoritative RP01 v002/v003 Blender libraries remain untouched and are
not promoted by this script.  The Blueprint architecture is built under the
new canonical /Game/LineBoss/Robots/Shared/RP01 path.  Its temporary visual
parts are isolated duplicates of the already import-gated CR01 v032 RP01
meshes; a 180-degree visual alignment component corrects that FBX candidate's
reversed X datum to the build-pack CFR (+X forward, +Y right, +Z up).

No AI, route following, charging logic, fault controller, physics movement or
SaveGame binding is implemented here.  The member variables and attachment
points are a reusable data/interface contract only.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE_ROOT = "/Game/LineBoss/Shared/SupportRobots/LB_CR01/Candidate_v032/LOD0"
CANDIDATE_ROOT = "/Game/LineBoss/Robots/Shared/RP01/Candidate_v001"
MESH_ROOT = CANDIDATE_ROOT + "/Meshes"
MATERIAL_ROOT = CANDIDATE_ROOT + "/Materials"
BP_ROOT = CANDIDATE_ROOT + "/Blueprints"
BP_PATH = BP_ROOT + "/BP_LB_RP01_MobileBase"
VALIDATION_MAP = "/Game/LineBoss/Developer/Validation/LB_RP01_MobileBase_Candidate_v001"
AUDIT = ROOT / "Saved/Audits/lb_rp01_mobile_base_candidate_v001_build.json"

asset_library = unreal.EditorAssetLibrary
bp_library = unreal.BlueprintEditorLibrary
subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
data_library = unreal.SubobjectDataBlueprintFunctionLibrary


SOURCE_SUFFIX = "_L_LB_RP01_SharedParts_v001_blend"

# These meshes cover the lower structural core, running gear, shared safety
# sensors, stack light, bumpers and common docking face.  They are duplicated,
# never moved or renamed in the v032 evidence location.
MESH_SOURCES = {
    "SM_LB_RP01_ChassisCore": "SM_LB_RP01_ChassisCore" + SOURCE_SUFFIX,
    "SM_LB_RP01_PayloadPlate": "SM_LB_RP01_PayloadPlate" + SOURCE_SUFFIX,
    "SM_LB_RP01_BumperFront": "SM_LB_RP01_BumperFront" + SOURCE_SUFFIX,
    "SM_LB_RP01_BumperRear": "SM_LB_RP01_BumperRear" + SOURCE_SUFFIX,
    "SM_LB_RP01_BumperSide_L": "SM_LB_RP01_BumperSide_L" + SOURCE_SUFFIX,
    "SM_LB_RP01_BumperSide_R": "SM_LB_RP01_BumperSide_R" + SOURCE_SUFFIX,
    "SM_LB_RP01_WheelShroud_L": "SM_LB_RP01_WheelShroud_L" + SOURCE_SUFFIX,
    "SM_LB_RP01_WheelShroud_R": "SM_LB_RP01_WheelShroud_R" + SOURCE_SUFFIX,
    "SM_LB_RP01_DriveWheel_L": "SM_LB_RP01_DriveWheel_L" + SOURCE_SUFFIX,
    "SM_LB_RP01_DriveWheel_R": "SM_LB_RP01_DriveWheel_R" + SOURCE_SUFFIX,
    "SM_LB_RP01_DriveRim_L": "SM_LB_RP01_DriveRim_L" + SOURCE_SUFFIX,
    "SM_LB_RP01_DriveRim_R": "SM_LB_RP01_DriveRim_R" + SOURCE_SUFFIX,
    "SM_LB_RP01_DriveHubCap_L": "SM_LB_RP01_DriveHubCap_L" + SOURCE_SUFFIX,
    "SM_LB_RP01_DriveHubCap_R": "SM_LB_RP01_DriveHubCap_R" + SOURCE_SUFFIX,
    "SM_LB_RP01_DriveBearing_L": "SM_LB_RP01_DriveBearing_L" + SOURCE_SUFFIX,
    "SM_LB_RP01_DriveBearing_R": "SM_LB_RP01_DriveBearing_R" + SOURCE_SUFFIX,
    "SM_LB_RP01_CasterForkArmA_F": "SM_LB_RP01_CasterForkArmA_F" + SOURCE_SUFFIX,
    "SM_LB_RP01_CasterForkArmB_F": "SM_LB_RP01_CasterForkArmB_F" + SOURCE_SUFFIX,
    "SM_LB_RP01_CasterForkArmA_R": "SM_LB_RP01_CasterForkArmA_R" + SOURCE_SUFFIX,
    "SM_LB_RP01_CasterForkArmB_R": "SM_LB_RP01_CasterForkArmB_R" + SOURCE_SUFFIX,
    "SM_LB_RP01_CasterSwivelBearing_F": "SM_LB_RP01_CasterSwivelBearing_F" + SOURCE_SUFFIX,
    "SM_LB_RP01_CasterSwivelBearing_R": "SM_LB_RP01_CasterSwivelBearing_R" + SOURCE_SUFFIX,
    "SM_LB_RP01_CasterWheel_F": "SM_LB_RP01_CasterWheel_F" + SOURCE_SUFFIX,
    "SM_LB_RP01_CasterWheel_R": "SM_LB_RP01_CasterWheel_R" + SOURCE_SUFFIX,
    "SM_LB_RP01_CasterRim_F": "SM_LB_RP01_CasterRim_F" + SOURCE_SUFFIX,
    "SM_LB_RP01_CasterRim_R": "SM_LB_RP01_CasterRim_R" + SOURCE_SUFFIX,
    "SM_LB_RP01_DockAlignmentPlate": "SM_LB_RP01_DockAlignmentPlate_v013" + SOURCE_SUFFIX,
    "SM_LB_RP01_DockGuideCone_L": "SM_LB_RP01_DockGuideCone_-120" + SOURCE_SUFFIX,
    "SM_LB_RP01_DockGuideCone_R": "SM_LB_RP01_DockGuideCone_120" + SOURCE_SUFFIX,
    "SM_LB_RP01_ChargingContact_N45": "SM_LB_RP01_ChargingContact_-45" + SOURCE_SUFFIX,
    "SM_LB_RP01_ChargingContact_P45": "SM_LB_RP01_ChargingContact_45" + SOURCE_SUFFIX,
    "SM_LB_RP01_FrontLiDAR": "SM_LB_RP01_FrontLiDAR",
    "SM_LB_RP01_DepthSensor_L": "SM_LB_RP01_DepthSensor_-150",
    "SM_LB_RP01_DepthSensor_C": "SM_LB_RP01_DepthSensor_0",
    "SM_LB_RP01_DepthSensor_R": "SM_LB_RP01_DepthSensor_150",
    "SM_LB_RP01_DepthCameraLens_L": "SM_LB_RP01_DepthCameraLens_-160",
    "SM_LB_RP01_DepthCameraLens_C": "SM_LB_RP01_DepthCameraLens_0",
    "SM_LB_RP01_DepthCameraLens_R": "SM_LB_RP01_DepthCameraLens_160",
    "SM_LB_RP01_Ultrasonic_FL": "SM_LB_RP01_Ultrasonic_600_-405" + SOURCE_SUFFIX,
    "SM_LB_RP01_Ultrasonic_FR": "SM_LB_RP01_Ultrasonic_600_405" + SOURCE_SUFFIX,
    "SM_LB_RP01_Ultrasonic_RL": "SM_LB_RP01_Ultrasonic_-600_-405" + SOURCE_SUFFIX,
    "SM_LB_RP01_Ultrasonic_RR": "SM_LB_RP01_Ultrasonic_-600_405" + SOURCE_SUFFIX,
    "SM_LB_RP01_StackLightMast": "SM_LB_RP01_StackLightMast" + SOURCE_SUFFIX,
    "SM_LB_RP01_StackLens_Red": "SM_LB_RP01_StackLens_Red" + SOURCE_SUFFIX,
    "SM_LB_RP01_StackLens_Amber": "SM_LB_RP01_StackLens_Amber" + SOURCE_SUFFIX,
    "SM_LB_RP01_StackLens_Green": "SM_LB_RP01_StackLens_Green" + SOURCE_SUFFIX,
    "SM_LB_RP01_StackLens_Blue": "SM_LB_RP01_StackLens_Blue" + SOURCE_SUFFIX,
}

MATERIAL_SOURCES = {
    "M_LB_RP01_FrameAnthracite": "M_LB_RP01_FrameAnthracite_v013",
    "M_LB_RP01_BodyCharcoal": "M_LB_RP01_BodyCharcoal_v013",
    "M_LB_RP01_RubberBlack": "M_LB_RP01_RubberBlack_v013",
    "M_LB_RP01_SafetyYellow": "M_LB_RP01_SafetyYellow_v013",
    "M_LB_RP01_LensVertexTint": "M_LB_RP01_LensVertexTint_v021",
    "M_LB_RP01_BrushedSteel": "M_LB_CR01_BrushedSteel_v013",
    "M_LB_RP01_SensorGlass": "M_LB_CR01_SensorGlass",
}

MATERIAL_NAME_MAP = {
    "M_LB_RP01_FrameAnthracite_v013": "M_LB_RP01_FrameAnthracite",
    "M_LB_RP01_BodyCharcoal_v013": "M_LB_RP01_BodyCharcoal",
    "M_LB_RP01_RubberBlack_v013": "M_LB_RP01_RubberBlack",
    "M_LB_RP01_SafetyYellow_v013": "M_LB_RP01_SafetyYellow",
    "M_LB_RP01_LensVertexTint_v021": "M_LB_RP01_LensVertexTint",
    "M_LB_CR01_BrushedSteel_v013": "M_LB_RP01_BrushedSteel",
    "M_LB_CR01_SensorGlass": "M_LB_RP01_SensorGlass",
}

# Build-pack authority: moving_parts_pivots.csv and sockets_interfaces.json,
# converted from millimetres to Unreal centimetres in the CFR frame.
ANCHORS = [
    ("PayloadInterface", None, (0.0, 0.0, 38.5), (0.0, 0.0, 0.0)),
    ("Attach_CR01_Payload", "PayloadInterface", (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
    ("Attach_MR01_Payload", "PayloadInterface", (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
    ("Attach_ConfigSpecificService", "PayloadInterface", (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
    ("Attach_DriveWheel_L", None, (-10.0, -40.5, 17.0), (0.0, 0.0, 0.0)),
    ("Attach_DriveWheel_R", None, (-10.0, 40.5, 17.0), (0.0, 0.0, 0.0)),
    ("Attach_Suspension_Front", None, (47.0, 0.0, 16.0), (0.0, 0.0, 0.0)),
    ("Attach_CasterRoll_Front", "Attach_Suspension_Front", (0.0, 0.0, -8.0), (0.0, 0.0, 0.0)),
    ("Attach_Suspension_Rear", None, (-53.0, 0.0, 16.0), (0.0, 0.0, 0.0)),
    ("Attach_CasterRoll_Rear", "Attach_Suspension_Rear", (0.0, 0.0, -8.0), (0.0, 0.0, 0.0)),
    ("Attach_Sensor_Front", None, (66.0, 0.0, 50.0), (0.0, 0.0, 0.0)),
    ("Attach_Sensor_Rear", None, (-66.0, 0.0, 50.0), (0.0, 0.0, 180.0)),
    ("Attach_Sensor_Left", None, (0.0, -41.0, 50.0), (0.0, 0.0, -90.0)),
    ("Attach_Sensor_Right", None, (0.0, 41.0, 50.0), (0.0, 0.0, 90.0)),
    ("Attach_DockDatum", None, (-73.5, 0.0, 31.0), (0.0, 0.0, 180.0)),
    ("Attach_ChargeContact_L", None, (-73.5, -12.0, 34.0), (0.0, 0.0, 180.0)),
    ("Attach_ChargeContact_R", None, (-73.5, 12.0, 34.0), (0.0, 0.0, 180.0)),
    ("Attach_NetworkContact", None, (-73.5, 0.0, 39.0), (0.0, 0.0, 180.0)),
    ("Attach_TowFront", None, (73.5, 0.0, 18.0), (0.0, 0.0, 0.0)),
    ("Attach_TowRear", None, (-73.5, 0.0, 18.0), (0.0, 0.0, 180.0)),
    ("Attach_AudioDrive_L", None, (-10.0, -40.5, 17.0), (0.0, 0.0, 0.0)),
    ("Attach_AudioDrive_R", None, (-10.0, 40.5, 17.0), (0.0, 0.0, 0.0)),
    ("Attach_AudioWarning", None, (-62.0, 0.0, 85.0), (0.0, 0.0, 180.0)),
]

VARIABLES = [
    ("PlatformModelId", "string", "LB-RP01"),
    ("RobotUniqueId", "string", "RP01-UNASSIGNED"),
    ("PayloadVariant", "string", "BASE"),
    ("BatteryChargePercent", "real", 100.0),
    ("BatteryHealthPercent", "real", 100.0),
    ("BatteryCapacityAh", "real", 105.0),
    ("ConditionState", "string", "RESTORED"),
    ("ConditionAgeYears", "real", 0.0),
    ("ConditionSeed", "int", 0),
    ("FaultCode", "string", ""),
    ("FaultLatched", "bool", False),
    ("CurrentRouteId", "string", ""),
    ("RouteProgress01", "real", 0.0),
    ("CurrentDockId", "string", ""),
    ("DockState", "string", "UNDOCKED"),
    ("IsDocked", "bool", False),
    ("IsEnabled", "bool", False),
    ("OperatingHours", "real", 0.0),
    ("ServiceCycles", "int", 0),
]


def path_for(source_name):
    return f"{SOURCE_ROOT}/{source_name}.{source_name}"


def require_asset(path, asset_type=None):
    asset = unreal.load_asset(path)
    if asset is None:
        raise RuntimeError(f"Missing required source asset {path}")
    if asset_type is not None and not isinstance(asset, asset_type):
        raise RuntimeError(f"Wrong class for {path}: {asset.get_class().get_name()}")
    return asset


def root_handle(blueprint):
    handles = subsystem.k2_gather_subobject_data_for_blueprint(blueprint)
    roots = []
    for handle in handles:
        data = subsystem.k2_find_subobject_data_from_handle(handle)
        if data_library.is_default_scene_root(data):
            roots.append(handle)
    if len(roots) != 1:
        raise RuntimeError(f"Expected exactly one DefaultSceneRoot, found {len(roots)}")
    return roots[0]


def add_component(blueprint, parent_handle, component_class, name):
    result = subsystem.add_new_subobject(params=unreal.AddNewSubobjectParams(
        parent_handle=parent_handle,
        new_class=component_class,
        blueprint_context=blueprint,
        conform_transform_to_parent=False,
        skip_mark_blueprint_modified=False,
    ))
    handle = result[0]
    failure = str(result[1]) if len(result) > 1 else ""
    if not data_library.is_handle_valid(handle):
        raise RuntimeError(f"Could not add {name}: {failure}")
    subsystem.rename_subobject(handle=handle, new_name=unreal.Text(name))
    data = subsystem.k2_find_subobject_data_from_handle(handle)
    component = data_library.get_object_for_blueprint(data, blueprint)
    if component is None:
        component = data_library.get_object(data)
    if component is None:
        raise RuntimeError(f"Could not resolve component template {name}")
    return handle, component


def set_relative(component, location, rotation=(0.0, 0.0, 0.0)):
    component.set_editor_property("relative_location", unreal.Vector(*location))
    component.set_editor_property("relative_rotation", unreal.Rotator(*rotation))
    component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)


def apply_canonical_material_overrides(component, static_mesh, materials):
    overrides = []
    for index, slot in enumerate(static_mesh.get_editor_property("static_materials")):
        source_material = slot.get_editor_property("material_interface")
        if source_material is None:
            continue
        source_name = source_material.get_name().removesuffix("_ncl_1")
        canonical_name = MATERIAL_NAME_MAP.get(source_name)
        if canonical_name and canonical_name in materials:
            component.set_material(index, materials[canonical_name])
            overrides.append({
                "slot": index,
                "source": source_material.get_path_name(),
                "canonical": materials[canonical_name].get_path_name(),
            })
    return overrides


for source_name in MESH_SOURCES.values():
    require_asset(path_for(source_name), unreal.StaticMesh)
for source_name in MATERIAL_SOURCES.values():
    require_asset(path_for(source_name), unreal.MaterialInterface)
for generated_path in (BP_PATH, VALIDATION_MAP):
    if asset_library.does_asset_exist(generated_path):
        raise RuntimeError(f"Preserve existing candidate; generated target already exists: {generated_path}")
if asset_library.does_directory_exist(CANDIDATE_ROOT):
    raise RuntimeError(f"Preserve existing candidate directory: {CANDIDATE_ROOT}")

materials = {}
material_rows = []
for destination_name, source_name in MATERIAL_SOURCES.items():
    source_path = path_for(source_name)
    destination_path = f"{MATERIAL_ROOT}/{destination_name}"
    if not asset_library.duplicate_asset(source_path, destination_path):
        raise RuntimeError(f"Could not duplicate material {source_path} -> {destination_path}")
    material = require_asset(destination_path, unreal.MaterialInterface)
    if not asset_library.save_loaded_asset(material, only_if_is_dirty=False):
        raise RuntimeError(f"Could not persist duplicated material {destination_path}")
    materials[destination_name] = material
    material_rows.append({"source": source_path, "candidate": material.get_path_name()})

meshes = {}
mesh_rows = []
for destination_name, source_name in MESH_SOURCES.items():
    source_path = path_for(source_name)
    destination_path = f"{MESH_ROOT}/{destination_name}"
    if not asset_library.duplicate_asset(source_path, destination_path):
        raise RuntimeError(f"Could not duplicate mesh {source_path} -> {destination_path}")
    mesh = require_asset(destination_path, unreal.StaticMesh)
    if not asset_library.save_loaded_asset(mesh, only_if_is_dirty=False):
        raise RuntimeError(f"Could not persist duplicated mesh {destination_path}")
    meshes[destination_name] = mesh
    box = mesh.get_bounding_box()
    mesh_rows.append({
        "source": source_path,
        "candidate": mesh.get_path_name(),
        "source_baked_bounds_centre_cm": list(((box.min + box.max) * 0.5).to_tuple()),
        "source_baked_bounds_size_cm": list((box.max - box.min).to_tuple()),
    })

blueprint = bp_library.create_blueprint_asset_with_parent(BP_PATH, unreal.Pawn)
if blueprint is None:
    raise RuntimeError(f"Could not create {BP_PATH}")
root = root_handle(blueprint)
handles = {}
component_rows = [{"component": "DefaultSceneRoot", "parent": None, "role": "sole_root"}]

static_handle, static_visuals = add_component(blueprint, root, unreal.SceneComponent, "VisualAlignment_v032")
set_relative(static_visuals, (0.0, 0.0, 0.0), (0.0, 0.0, 180.0))
handles["VisualAlignment_v032"] = static_handle
component_rows.append({
    "component": "VisualAlignment_v032",
    "parent": "DefaultSceneRoot",
    "role": "temporary_v032_visual_axis_correction",
    "relative_rotation_deg": [0.0, 0.0, 180.0],
})

for name, parent_name, location, rotation in ANCHORS:
    parent = handles[parent_name] if parent_name else root
    handle, component = add_component(blueprint, parent, unreal.SceneComponent, name)
    set_relative(component, location, rotation)
    component.set_editor_property("component_tags", [unreal.Name(f"LB.RP01.Anchor.{name}")])
    handles[name] = handle
    component_rows.append({
        "component": name,
        "parent": parent_name or "DefaultSceneRoot",
        "role": "shared_interface_anchor",
        "relative_location_cm": list(location),
        "relative_rotation_deg": list(rotation),
    })

# Visual components are divided by articulation datum.  Their source vertices
# are baked in v032 assembly space, so articulated groups use -source-pivot plus
# a 180-degree yaw; this preserves their default assembly pose while making the
# anchor a correct future rotation point.
DRIVE_L = {"SM_LB_RP01_DriveWheel_L", "SM_LB_RP01_DriveRim_L", "SM_LB_RP01_DriveHubCap_L", "SM_LB_RP01_DriveBearing_L"}
DRIVE_R = {"SM_LB_RP01_DriveWheel_R", "SM_LB_RP01_DriveRim_R", "SM_LB_RP01_DriveHubCap_R", "SM_LB_RP01_DriveBearing_R"}
CASTER_FORK_F = {"SM_LB_RP01_CasterForkArmA_F", "SM_LB_RP01_CasterForkArmB_F", "SM_LB_RP01_CasterSwivelBearing_F"}
CASTER_FORK_R = {"SM_LB_RP01_CasterForkArmA_R", "SM_LB_RP01_CasterForkArmB_R", "SM_LB_RP01_CasterSwivelBearing_R"}
CASTER_ROLL_F = {"SM_LB_RP01_CasterWheel_F", "SM_LB_RP01_CasterRim_F"}
CASTER_ROLL_R = {"SM_LB_RP01_CasterWheel_R", "SM_LB_RP01_CasterRim_R"}
DOCK = {"SM_LB_RP01_DockAlignmentPlate", "SM_LB_RP01_DockGuideCone_L", "SM_LB_RP01_DockGuideCone_R", "SM_LB_RP01_ChargingContact_N45", "SM_LB_RP01_ChargingContact_P45"}

source_pivots = {
    "Attach_DriveWheel_L": (10.0, 40.5, 17.0),
    "Attach_DriveWheel_R": (10.0, -40.5, 17.0),
    "Attach_Suspension_Front": (-47.0, 0.0, 16.0),
    "Attach_Suspension_Rear": (53.0, 0.0, 16.0),
    "Attach_CasterRoll_Front": (-47.0, 0.0, 8.0),
    "Attach_CasterRoll_Rear": (53.0, 0.0, 8.0),
    "Attach_DockDatum": (73.5, 0.0, 31.0),
}


def visual_parent_and_transform(mesh_name):
    if mesh_name in DRIVE_L:
        parent_name = "Attach_DriveWheel_L"
    elif mesh_name in DRIVE_R:
        parent_name = "Attach_DriveWheel_R"
    elif mesh_name in CASTER_FORK_F:
        parent_name = "Attach_Suspension_Front"
    elif mesh_name in CASTER_FORK_R:
        parent_name = "Attach_Suspension_Rear"
    elif mesh_name in CASTER_ROLL_F:
        parent_name = "Attach_CasterRoll_Front"
    elif mesh_name in CASTER_ROLL_R:
        parent_name = "Attach_CasterRoll_Rear"
    elif mesh_name in DOCK:
        parent_name = "Attach_DockDatum"
    else:
        return "VisualAlignment_v032", (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)
    source_pivot = source_pivots[parent_name]
    return parent_name, tuple(-value for value in source_pivot), (0.0, 0.0, 180.0)


for mesh_name, mesh in meshes.items():
    parent_name, location, rotation = visual_parent_and_transform(mesh_name)
    handle, component = add_component(blueprint, handles[parent_name], unreal.StaticMeshComponent, f"Visual_{mesh_name.removeprefix('SM_LB_RP01_')}")
    component.set_static_mesh(mesh)
    set_relative(component, location, rotation)
    component.set_editor_property("component_tags", [unreal.Name("LB.RP01.Visual.CandidateNotPromoted")])
    overrides = apply_canonical_material_overrides(component, mesh, materials)
    component_rows.append({
        "component": f"Visual_{mesh_name.removeprefix('SM_LB_RP01_')}",
        "parent": parent_name,
        "role": "temporary_shared_visual",
        "mesh": mesh.get_path_name(),
        "relative_location_cm": list(location),
        "relative_rotation_deg": list(rotation),
        "canonical_material_overrides": overrides,
    })

variable_rows = []
for name, type_name, default in VARIABLES:
    pin_type = bp_library.get_basic_type_by_name(type_name)
    if not bp_library.add_member_variable(blueprint, name, pin_type):
        raise RuntimeError(f"Could not add {name}:{type_name}")
    bp_library.set_blueprint_variable_instance_editable(blueprint, name, True)
    variable_rows.append({"name": name, "type": type_name, "default": default, "instance_editable": True})

bp_library.compile_blueprint(blueprint)
generated_class = bp_library.generated_class(blueprint)
if generated_class is None:
    raise RuntimeError("RP01 Blueprint generated class is missing after compile")
default_object = unreal.get_default_object(generated_class)
for name, _type_name, default in VARIABLES:
    default_object.set_editor_property(name, default)
default_object.set_editor_property("tags", [
    unreal.Name("LB.Asset.CandidateNotPromoted"),
    unreal.Name("LB.Robot.Platform.RP01"),
    unreal.Name("LB.Robot.SharedBase"),
])
if not asset_library.save_loaded_asset(blueprint, only_if_is_dirty=False):
    raise RuntimeError(f"Could not save {BP_PATH}")

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.new_level(VALIDATION_MAP):
    raise RuntimeError(f"Could not create validation map {VALIDATION_MAP}")
robot = actors.spawn_actor_from_class(generated_class, unreal.Vector(0.0, 0.0, 0.0), unreal.Rotator())
if robot is None:
    raise RuntimeError("Could not spawn RP01 validation instance")
robot.set_actor_label("LB_RP01_MobileBase_Candidate_v001")
validation_state = {
    "RobotUniqueId": "RP01-VALIDATION-001",
    "PayloadVariant": "BASE",
    "BatteryChargePercent": 64.0,
    "ConditionState": "MOTHBALLED",
    "ConditionAgeYears": 7.0,
    "ConditionSeed": 1001,
    "FaultCode": "RESTORATION_REQUIRED",
    "FaultLatched": True,
    "CurrentRouteId": "VALIDATION_ROUTE",
    "RouteProgress01": 0.25,
    "CurrentDockId": "RP01-DOCK-VALIDATION",
    "DockState": "UNDOCKED",
    "IsDocked": False,
    "IsEnabled": False,
    "OperatingHours": 12480.0,
    "ServiceCycles": 88200,
}
for name, value in validation_state.items():
    robot.set_editor_property(name, value)
robot.set_editor_property("tags", [
    unreal.Name("LB.Asset.CandidateNotPromoted"),
    unreal.Name("LB.Validation.RP01.MobileBase"),
])
if not levels.save_current_level():
    raise RuntimeError(f"Could not save validation map {VALIDATION_MAP}")

payload = {
    "$schema": "line-boss/audit/lb-rp01-mobile-base-candidate-v001-build/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "CANONICAL_PATH_SHARED_MOBILE_BASE_ARCHITECTURE_BUILT__TECHNICAL_AUDIT_REQUIRED__NOT_PROMOTED",
    "authoritative_contracts": [
        "SourceAssets/ReferencePacks/LB_CR01_SHARED_ROBOT_PLATFORM_BUILD_PACK_v1.0/data/authoritative_dimensions.json",
        "SourceAssets/ReferencePacks/LB_CR01_SHARED_ROBOT_PLATFORM_BUILD_PACK_v1.0/data/moving_parts_pivots.csv",
        "SourceAssets/ReferencePacks/LB_CR01_SHARED_ROBOT_PLATFORM_BUILD_PACK_v1.0/data/sockets_interfaces.json",
        "SourceAssets/ReferencePacks/LB_MR01_SHARED_PLATFORM_BUILD_PACK_v1.0/DEPENDENCY_CONTRACT.md",
    ],
    "rp01_blender_source": "SourceAssets/Robots/LB_RP01_Shared/Blender/Candidate_v002/LB_RP01_SharedParts_v002.blend",
    "rp01_v003_origin_normalisation": "PASS_WITH_ZERO_CHANGES__WORLD_SPACE_UNCHANGED",
    "standalone_rp01_v002_export_present": False,
    "temporary_visual_source": SOURCE_ROOT,
    "temporary_visual_source_gate": "V032_IMPORT_BOUNDS_PASS__VISUAL_AND_RUNTIME_GATES_OPEN",
    "visual_axis_correction": "180_DEG_YAW_TO_RESTORE_BUILD_PACK_CFR_PLUS_X_FORWARD",
    "candidate_root": CANDIDATE_ROOT,
    "blueprint": BP_PATH,
    "parent_class": "Pawn",
    "validation_map": VALIDATION_MAP,
    "validation_actor": robot.get_actor_label(),
    "validation_state": validation_state,
    "sole_root_component": "DefaultSceneRoot",
    "attachment_anchor_count": len(ANCHORS),
    "components": component_rows,
    "instance_variables": variable_rows,
    "duplicated_meshes": mesh_rows,
    "duplicated_mesh_count": len(mesh_rows),
    "duplicated_materials": material_rows,
    "duplicated_material_count": len(material_rows),
    "source_assets_modified": False,
    "implemented": [
        "canonical-path reusable Pawn parent",
        "single scene root",
        "shared payload and CR01/MR01 extension anchors",
        "drive-wheel and caster suspension/roll anchors",
        "sensor, docking, tow and audio attachment anchors",
        "instance-editable identity, battery, condition, fault, route and dock data fields",
        "isolated candidate visual/material duplicates",
    ],
    "open_gates": [
        "fresh independent Blueprint compile/hierarchy/type/default/instance audit",
        "standalone RP01 v002/v003 export and import regression",
        "CR01 child Blueprint composition",
        "MR01 child Blueprint composition",
        "movement component and autonomous route controller",
        "docking/charging state machine and interlocks",
        "fault transition controller",
        "SaveGame serialization and round-trip",
        "release collision, navigation and swept movement",
        "fresh fixed-camera screenshots against CR01 and MR01 Pro references",
    ],
    "runtime_ai_implemented": False,
    "savegame_binding_implemented": False,
    "release_collision_implemented": False,
    "promotion_authorized": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(
    f"LINE_BOSS_RP01_MOBILE_BASE_CANDIDATE_V001_BUILD_PASS "
    f"meshes={len(mesh_rows)} anchors={len(ANCHORS)} variables={len(VARIABLES)} audit={AUDIT}"
)
unreal.SystemLibrary.quit_editor()
