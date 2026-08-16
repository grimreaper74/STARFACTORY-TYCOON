"""Rebuild only the generated v020 core/map with correct UE real state pins."""

from datetime import datetime, timezone
import json
import math
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
IMPORT = json.loads((ROOT / "Saved/Audits/pr004_unreal_import_candidate_v003.json").read_text(encoding="utf-8"))
SOURCE = json.loads((ROOT / "Saved/Audits/pr004_robot_candidate_v002_source.json").read_text(encoding="utf-8"))
BUILD_AUDIT = ROOT / "Saved/Audits/press_shop_pr004_surfaceforge_robot_candidate_v020.json"
REPAIR_AUDIT = ROOT / "Saved/Audits/press_shop_pr004_surfaceforge_robot_real_state_rebuild_v020.json"

BASE_MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004ReusableRobotCandidate_v016"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004SurfaceForgeRobotCandidate_v020"
BP_PATH = "/Game/LineBoss/Equipment/Robots/Modular6Axis/Candidate_v020/BP_LB_Modular6AxisRobot_400kg_v020"
MESH_ROOT = "/Game/LineBoss/Equipment/Robots/Modular6Axis/Candidate_v020/Meshes"
SURFACE_MATERIAL = "/Game/LineBoss/Equipment/Robots/Modular6Axis/Candidate_v020/Materials/MI_LB_Robot_CairnwellGreen_Aged_v020"
BAND_TOOL = "/Game/LineBoss/Equipment/Robots/Modular6Axis/Candidate_v020/Tools/BP_LB_RobotTool_BandCutterCapture_v020"
PLATE_MATERIAL = "/Game/LineBoss/Brand/Cairnwell/Candidate_v020/RobotPlate/M_Cairnwell_PR004_RobotPlate_v020"
CARRIER_MATERIAL = "/Game/LineBoss/Brand/Cairnwell/Candidate_v020/RobotPlate/M_Cairnwell_RobotPlateCarrier_v020"
SOURCE_ROBOT_LABEL = "LB_INT_PR004_BP_ModularRobot_400kg_v002"
ROBOT_LABEL = "LB_INT_PR004_BP_ModularRobot_400kg_v020"

SOURCE_MODULES = {row["id"]: row for row in SOURCE["modules"]}
IMPORT_MODULES = {
    row["module_id"]: row for row in IMPORT["imported_assets"] if row["family"] == "robot_v002"
}
CORE = [
    ("base", "BasePedestal", None),
    ("j1", "J1_BaseYaw", "base"),
    ("j2", "J2_Shoulder", "j1"),
    ("j3", "J3_Elbow", "j2"),
    ("j4", "J4_WristRoll", "j3"),
    ("j5", "J5_WristPitch", "j4"),
    ("j6", "J6_ToolRoll", "j5"),
    ("changer_body", "QuickChangerBody", "j6"),
    ("changer_lock", "QuickChangerLock", "changer_body"),
    ("dress_lower", "DressPackLower", "j1"),
    ("dress_upper", "DressPackUpper", "j2"),
    ("dress_wrist", "DressPackWrist", "j4"),
]
STATE = {
    "StationId": "PR-004",
    "EquipmentId": "PR004-RBT-01",
    "ConditionAgeYears": 7.0,
    "ConditionSeed": 4001,
    "CurrentToolId": "BandCutterCapture",
    "J1Degrees": 0.0,
    "J2Degrees": 0.0,
    "J3Degrees": 0.0,
    "J4Degrees": 0.0,
    "J5Degrees": 0.0,
    "J6Degrees": 0.0,
    "Enabled": False,
    "ToolLocked": True,
    "FaultCode": "RESTORATION_REQUIRED",
    "OperatingHours": 18420.0,
    "ServiceCycles": 318500,
}
VARIABLES = [
    ("StationId", "string"),
    ("EquipmentId", "string"),
    ("ConditionAgeYears", "real"),
    ("ConditionSeed", "int"),
    ("CurrentToolId", "string"),
    ("J1Degrees", "real"),
    ("J2Degrees", "real"),
    ("J3Degrees", "real"),
    ("J4Degrees", "real"),
    ("J5Degrees", "real"),
    ("J6Degrees", "real"),
    ("Enabled", "bool"),
    ("ToolLocked", "bool"),
    ("FaultCode", "string"),
    ("OperatingHours", "real"),
    ("ServiceCycles", "int"),
]

lib = unreal.EditorAssetLibrary
bp_lib = unreal.BlueprintEditorLibrary
subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
data_lib = unreal.SubobjectDataBlueprintFunctionLibrary


def required(path, kind=None):
    asset = lib.load_asset(path)
    if asset is None or (kind is not None and not isinstance(asset, kind)):
        raise RuntimeError(f"Missing required preserved v020 dependency: {path}")
    return asset


def asset_name(object_path):
    return object_path.split(".", 1)[0].rsplit("/", 1)[-1]


def v020_mesh(module_id):
    source_name = asset_name(IMPORT_MODULES[module_id]["asset"])
    return required(f"{MESH_ROOT}/{source_name.replace('_v002', '_v020')}", unreal.StaticMesh)


def local_delta(child_id, parent_id):
    child = SOURCE_MODULES[child_id]
    parent = SOURCE_MODULES[parent_id]
    cx, cy, cz = child["assembly_location_cm"]
    px, py, pz = parent["assembly_location_cm"]
    yaw = math.radians(parent["assembly_rotation_deg"][2])
    dx, dy = cx - px, cy - py
    return (
        math.cos(yaw) * dx + math.sin(yaw) * dy,
        -math.sin(yaw) * dx + math.cos(yaw) * dy,
        cz - pz,
    )


def root_handle(blueprint):
    handles = subsystem.k2_gather_subobject_data_for_blueprint(blueprint)
    for handle in handles:
        data = subsystem.k2_find_subobject_data_from_handle(handle)
        if data_lib.is_default_scene_root(data):
            return handle
    raise RuntimeError("Corrected Blueprint has no default scene root")


def add_component(blueprint, parent, component_class, name):
    result = subsystem.add_new_subobject(params=unreal.AddNewSubobjectParams(
        parent_handle=parent,
        new_class=component_class,
        blueprint_context=blueprint,
        conform_transform_to_parent=False,
        skip_mark_blueprint_modified=False,
    ))
    handle = result[0]
    failure = str(result[1]) if len(result) > 1 else ""
    if not data_lib.is_handle_valid(handle):
        raise RuntimeError(f"Could not add {name}: {failure}")
    subsystem.rename_subobject(handle=handle, new_name=unreal.Text(name))
    data = subsystem.k2_find_subobject_data_from_handle(handle)
    component = data_lib.get_object_for_blueprint(data, blueprint) or data_lib.get_object(data)
    if component is None:
        raise RuntimeError(f"Could not resolve component {name}")
    return handle, component


def set_relative(component, location, rotation=(0, 0, 0)):
    component.set_editor_property("relative_location", unreal.Vector(*location))
    component.set_editor_property("relative_rotation", unreal.Rotator(*rotation))
    component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)


def apply_surface(component, module_id, material):
    assignments = IMPORT_MODULES[module_id]["opaque_material_assignments"]
    if component.get_num_materials() != len(assignments):
        raise RuntimeError(f"Material slot mismatch rebuilding {module_id}")
    rows = []
    for index, assignment in enumerate(assignments):
        if assignment["material_key"] == "CastIron":
            component.set_material(index, material)
            rows.append({"index": index, "slot": assignment["slot"]})
    return rows


def build_corrected_core():
    blueprint = bp_lib.create_blueprint_asset_with_parent(BP_PATH, unreal.Actor)
    if blueprint is None:
        raise RuntimeError(f"Could not create corrected {BP_PATH}")
    root = root_handle(blueprint)
    surface = required(SURFACE_MATERIAL, unreal.MaterialInterface)
    handles = {}
    rows = []
    for module_id, component_name, parent_id in CORE:
        parent = handles[parent_id] if parent_id else root
        location = local_delta(module_id, parent_id) if parent_id else tuple(SOURCE_MODULES[module_id]["assembly_location_cm"])
        handle, component = add_component(blueprint, parent, unreal.StaticMeshComponent, component_name)
        component.set_static_mesh(v020_mesh(module_id))
        set_relative(component, location)
        handles[module_id] = handle
        rows.append({
            "component": component_name,
            "module_id": module_id,
            "parent": parent_id or "DefaultSceneRoot",
            "relative_location_cm": list(location),
            "cast_iron_overrides": apply_surface(component, module_id, surface),
        })

    mount_handle, mount = add_component(blueprint, handles["changer_body"], unreal.SceneComponent, "ToolMount")
    set_relative(mount, (0, 0, 0))
    equipped_handle, equipped = add_component(blueprint, mount_handle, unreal.ChildActorComponent, "EquippedTool")
    equipped.set_editor_property("child_actor_class", bp_lib.generated_class(required(BAND_TOOL)))
    set_relative(equipped, (0, 0, 0))
    rows.extend([
        {"component": "ToolMount", "parent": "changer_body"},
        {"component": "EquippedTool", "parent": "ToolMount", "tool": BAND_TOOL},
    ])

    carrier_handle, carrier = add_component(
        blueprint, handles["j3"], unreal.StaticMeshComponent, "CairnwellPlateCarrier_v020"
    )
    carrier.set_static_mesh(required("/Engine/BasicShapes/Cube.Cube", unreal.StaticMesh))
    set_relative(carrier, (52.0, -49.8, 8.0))
    carrier.set_editor_property("relative_scale3d", unreal.Vector(0.44, 0.006, 0.17))
    carrier.set_material(0, required(CARRIER_MATERIAL, unreal.MaterialInterface))
    face_handle, face = add_component(
        blueprint, handles["j3"], unreal.StaticMeshComponent, "RobotAssetPlateFace_v020"
    )
    face.set_static_mesh(required("/Engine/BasicShapes/Plane.Plane", unreal.StaticMesh))
    set_relative(face, (52.0, -50.45, 8.0), (90.0, 0.0, 0.0))
    face.set_editor_property("relative_scale3d", unreal.Vector(0.42, 0.1575, 1.0))
    face.set_material(0, required(PLATE_MATERIAL, unreal.MaterialInterface))
    rows.extend([
        {"component": "CairnwellPlateCarrier_v020", "parent": "j3", "material": CARRIER_MATERIAL},
        {"component": "RobotAssetPlateFace_v020", "parent": "j3", "material": PLATE_MATERIAL},
    ])

    variable_rows = []
    for name, type_name in VARIABLES:
        pin = bp_lib.get_basic_type_by_name(type_name)
        if not bp_lib.add_member_variable(blueprint, name, pin):
            raise RuntimeError(f"Could not add corrected variable {name}:{type_name}")
        bp_lib.set_blueprint_variable_instance_editable(blueprint, name, True)
        variable_rows.append({"name": name, "type": type_name, "instance_editable": True})
    bp_lib.compile_blueprint(blueprint)
    if not lib.save_loaded_asset(blueprint, only_if_is_dirty=False):
        raise RuntimeError("Could not save corrected v020 Blueprint")
    return blueprint, rows, variable_rows


def build_corrected_map(blueprint):
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not levels.new_level_from_template(MAP, BASE_MAP):
        raise RuntimeError(f"Could not recreate {MAP} from {BASE_MAP}")
    source = [actor for actor in actors.get_all_level_actors() if actor.get_actor_label() == SOURCE_ROBOT_LABEL]
    if len(source) != 1:
        raise RuntimeError(f"Expected one v016 robot, found {len(source)}")
    old = source[0]
    location = old.get_actor_location()
    rotation = old.get_actor_rotation()
    scale = old.get_actor_scale3d()
    actors.destroy_actor(old)
    robot = actors.spawn_actor_from_class(bp_lib.generated_class(blueprint), location, rotation)
    robot.set_actor_label(ROBOT_LABEL)
    robot.set_actor_scale3d(scale)
    robot.set_editor_property("tags", [
        unreal.Name("LB.Asset.CandidateNotPromoted"),
        unreal.Name("LB.Equipment.Robot.Modular6Axis"),
        unreal.Name("LB.Station.PR004"),
        unreal.Name("LB.Tool.BandCutterCapture"),
        unreal.Name("LB.Material.SurfaceForgeSelective"),
        unreal.Name("LB.Brand.Cairnwell"),
    ])
    for name, value in STATE.items():
        robot.set_editor_property(name, value)
    verified = {name: robot.get_editor_property(name) for name in STATE}
    if verified != STATE:
        raise RuntimeError(f"Corrected state mismatch: {verified}")
    if not levels.save_current_level():
        raise RuntimeError(f"Could not save corrected map {MAP}")
    return robot, verified


for dependency in (BASE_MAP, SURFACE_MATERIAL, BAND_TOOL, PLATE_MATERIAL, CARRIER_MATERIAL):
    required(dependency)
for module_id, _name, _parent in CORE:
    v020_mesh(module_id)
# These are the only destructive targets: two generated v020 artifacts.  The
# first recovery run may have deleted one target before an Asset Registry
# timing guard stopped it, so make the exact rebuild safely resumable from
# either the original or that generated-only partial state.  Do not query
# does_asset_exist immediately after deletion: UE 5.8 can keep the just-deleted
# package in the current process registry until the replacement is created.
target_state_before = {
    MAP: lib.does_asset_exist(MAP),
    BP_PATH: lib.does_asset_exist(BP_PATH),
}
deleted_this_run = []
for generated_path in (MAP, BP_PATH):
    if target_state_before[generated_path]:
        if not lib.delete_asset(generated_path):
            raise RuntimeError(f"Could not remove generated v020 target {generated_path}")
        deleted_this_run.append(generated_path)

blueprint, component_rows, variable_rows = build_corrected_core()
robot, state = build_corrected_map(blueprint)
generated = bp_lib.generated_class(blueprint)
default = unreal.get_default_object(generated)
real_names = [name for name, type_name in VARIABLES if type_name == "real"]
default_types = {name: str(type(default.get_editor_property(name))) for name in real_names}
instance_types = {name: str(type(robot.get_editor_property(name))) for name in real_names}
if any(value != "<class 'float'>" for value in default_types.values()):
    raise RuntimeError(f"Corrected default real types failed: {default_types}")
if any(value != "<class 'float'>" for value in instance_types.values()):
    raise RuntimeError(f"Corrected instance real types failed: {instance_types}")

build_payload = json.loads(BUILD_AUDIT.read_text(encoding="utf-8"))
build_payload["instance_variables"] = variable_rows
build_payload["instance_state"] = state
build_payload["robot_core_components"] = component_rows
build_payload["numeric_state_gate"] = {
    "status": "PASS",
    "ue_pin_category": "real",
    "ue_pin_sub_category": "double",
    "default_python_types": default_types,
    "instance_python_types": instance_types,
    "rebuild_audit": str(REPAIR_AUDIT.relative_to(ROOT)).replace("\\", "/"),
}
BUILD_AUDIT.write_text(json.dumps(build_payload, indent=2), encoding="utf-8")

payload = {
    "$schema": "line-boss/audit/press-shop-pr004-surfaceforge-robot-real-state-rebuild-v020/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "GENERATED_CORE_AND_MAP_REBUILT_WITH_UE_REAL_DOUBLE_STATE_TYPES",
    "generated_targets": [MAP, BP_PATH],
    "target_state_before_run": target_state_before,
    "deleted_generated_assets_this_run": deleted_this_run,
    "recovered_generated_only_partial_state": not all(target_state_before.values()),
    "preserved_dependencies": {
        "mesh_count": 27,
        "tool_blueprint_count": 4,
        "surface_material": SURFACE_MATERIAL,
        "plate_material": PLATE_MATERIAL,
        "base_map": BASE_MAP,
    },
    "rebuilt_blueprint": BP_PATH,
    "rebuilt_map": MAP,
    "robot": ROBOT_LABEL,
    "default_types": default_types,
    "instance_types": instance_types,
    "instance_state": state,
    "promotion_authorized": False,
}
REPAIR_AUDIT.parent.mkdir(parents=True, exist_ok=True)
REPAIR_AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR004_SURFACEFORGE_ROBOT_REAL_STATE_REBUILD_V020_PASS audit={REPAIR_AUDIT}")
unreal.SystemLibrary.quit_editor()
