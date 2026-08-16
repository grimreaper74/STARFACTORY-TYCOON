"""Author reusable candidate Blueprints for the PR-004 robot core and four tools."""

import json
import math
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
IMPORT = json.loads((ROOT / "Saved/Audits/pr004_unreal_import_candidate_v003.json").read_text(encoding="utf-8"))
SOURCE = json.loads((ROOT / "Saved/Audits/pr004_robot_candidate_v002_source.json").read_text(encoding="utf-8"))
CONTRACT = ROOT / "SourceAssets/PR004/RoboticDepackRobot/LB_Modular6AxisRobot_ReusableContract_v005.json"
AUDIT = ROOT / "Saved/Audits/reusable_modular_robot_blueprints_v005.json"
ASSET_ROOT = "/Game/LineBoss/Equipment/Robots/Modular6Axis/Candidate_v005"
TOOL_ROOT = ASSET_ROOT + "/Tools"

lib = unreal.EditorAssetLibrary
bp_lib = unreal.BlueprintEditorLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
material_lib = unreal.MaterialEditingLibrary
subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
data_lib = unreal.SubobjectDataBlueprintFunctionLibrary

mesh_paths = {row["module_id"]: row["asset"] for row in IMPORT["imported_assets"] if row["family"] == "robot_v002"}
source_modules = {row["id"]: row for row in SOURCE["modules"]}


def create_blueprint(path):
    if lib.does_asset_exist(path):
        if not lib.delete_asset(path):
            raise RuntimeError(f"Could not replace generated candidate {path}")
    bp = bp_lib.create_blueprint_asset_with_parent(path, unreal.Actor)
    if bp is None:
        raise RuntimeError(f"Could not create Blueprint {path}")
    return bp


def root_handle(bp):
    handles = subsystem.k2_gather_subobject_data_for_blueprint(bp)
    for handle in handles:
        data = subsystem.k2_find_subobject_data_from_handle(handle)
        if data_lib.is_default_scene_root(data):
            return handle
    if not handles:
        raise RuntimeError(f"Blueprint has no subobject handles: {bp.get_path_name()}")
    return handles[-1]


def add_component(bp, parent, component_class, name):
    params = unreal.AddNewSubobjectParams(
        parent_handle=parent,
        new_class=component_class,
        blueprint_context=bp,
        conform_transform_to_parent=False,
        skip_mark_blueprint_modified=False,
    )
    result = subsystem.add_new_subobject(params=params)
    handle = result[0]
    failure = str(result[1]) if len(result) > 1 else ""
    if not data_lib.is_handle_valid(handle):
        raise RuntimeError(f"Could not add {name}: {failure}")
    subsystem.rename_subobject(handle=handle, new_name=unreal.Text(name))
    data = subsystem.k2_find_subobject_data_from_handle(handle)
    component = data_lib.get_object_for_blueprint(data, bp)
    if component is None:
        component = data_lib.get_object(data)
    if component is None:
        raise RuntimeError(f"Could not resolve component template {name}")
    return handle, component


def set_relative(component, location, rotation=(0.0, 0.0, 0.0)):
    component.set_editor_property("relative_location", unreal.Vector(*location))
    component.set_editor_property("relative_rotation", unreal.Rotator(*rotation))
    component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)


def add_mesh(bp, parent, module_id, name, location, rotation=(0.0, 0.0, 0.0)):
    handle, component = add_component(bp, parent, unreal.StaticMeshComponent, name)
    mesh = lib.load_asset(mesh_paths[module_id])
    if mesh is None:
        raise RuntimeError(f"Missing mesh for {module_id}: {mesh_paths[module_id]}")
    component.set_static_mesh(mesh)
    set_relative(component, location, rotation)
    return handle, component


def local_delta(child_id, parent_id):
    child = source_modules[child_id]
    parent = source_modules[parent_id]
    cx, cy, cz = child["assembly_location_cm"]
    px, py, pz = parent["assembly_location_cm"]
    yaw = math.radians(parent["assembly_rotation_deg"][2])
    dx, dy = cx - px, cy - py
    return (
        math.cos(yaw) * dx + math.sin(yaw) * dy,
        -math.sin(yaw) * dx + math.cos(yaw) * dy,
        cz - pz,
    )


def build_tool(path, body_id, children, location_overrides=None):
    bp = create_blueprint(path)
    root = root_handle(bp)
    body_handle, _body = add_mesh(bp, root, body_id, "ToolBody", (0.0, 0.0, 0.0))
    records = [{"component": "ToolBody", "module_id": body_id, "parent": "DefaultSceneRoot", "relative_location_cm": [0, 0, 0]}]
    for child_id, component_name in children:
        location = (location_overrides or {}).get(child_id, local_delta(child_id, body_id))
        add_mesh(bp, body_handle, child_id, component_name, location)
        records.append({"component": component_name, "module_id": child_id, "parent": "ToolBody", "relative_location_cm": list(location)})
    bp_lib.compile_blueprint(bp)
    if not lib.save_loaded_asset(bp, only_if_is_dirty=False):
        raise RuntimeError(f"Could not save {path}")
    return {"asset": path, "body": body_id, "components": records}


band_working_offsets = {
    "band_left_capture": (45.0, -28.0, 0.0),
    "band_right_capture": (45.0, 28.0, 0.0),
    "band_cutter": (60.0, 0.0, 0.0),
    "band_roll_left": (45.0, -28.0, -15.0),
    "band_roll_right": (45.0, 28.0, -15.0),
}
tools = [
    build_tool(TOOL_ROOT + "/BP_LB_RobotTool_BandCutterCapture_v005", "band_tool", [
        ("band_left_capture", "LeftCaptureJaw"), ("band_right_capture", "RightCaptureJaw"),
        ("band_cutter", "BandCutter"), ("band_roll_left", "LeftWithdrawalRoll"),
        ("band_roll_right", "RightWithdrawalRoll"),
    ], band_working_offsets),
    build_tool(TOOL_ROOT + "/BP_LB_RobotTool_WrapPeelerVacuum_v005", "wrap_tool", [
        ("wrap_vacuum_carrier", "VacuumCarrier"), ("wrap_peel_roll", "PeelRoll"),
    ]),
    build_tool(TOOL_ROOT + "/BP_LB_RobotTool_EdgeProtectorGripper_v005", "edge_tool", [
        ("edge_left_jaw", "LeftJaw"), ("edge_right_jaw", "RightJaw"),
    ]),
    build_tool(TOOL_ROOT + "/BP_LB_RobotTool_LabelRFIDInspection_v005", "inspection_tool", [
        ("inspection_bore_camera", "BoreCamera"), ("inspection_shutter", "CameraShutter"),
    ]),
]

brand_material_root = "/Game/LineBoss/Brand/Cairnwell/Candidate_v004/Robot"
plate_material_path = brand_material_root + "/M_Cairnwell_RobotPlateCarrier_v005"
plate_material = lib.load_asset(plate_material_path)
if plate_material is None:
    plate_material = asset_tools.create_asset(
        "M_Cairnwell_RobotPlateCarrier_v005", brand_material_root,
        unreal.Material, unreal.MaterialFactoryNew(),
    )
    colour = material_lib.create_material_expression(plate_material, unreal.MaterialExpressionConstant3Vector, -350, -40)
    colour.set_editor_property("constant", unreal.LinearColor(0.90, 0.88, 0.82, 1.0))
    rough = material_lib.create_material_expression(plate_material, unreal.MaterialExpressionConstant, -350, 120)
    rough.set_editor_property("r", 0.58)
    metal = material_lib.create_material_expression(plate_material, unreal.MaterialExpressionConstant, -350, 200)
    metal.set_editor_property("r", 0.12)
    material_lib.connect_material_property(colour, "", unreal.MaterialProperty.MP_BASE_COLOR)
    material_lib.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    material_lib.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    material_lib.recompile_material(plate_material)
    lib.save_loaded_asset(plate_material, only_if_is_dirty=False)

core_path = ASSET_ROOT + "/BP_LB_Modular6AxisRobot_400kg_v005"
core = create_blueprint(core_path)
root = root_handle(core)
handles = {}
components = []
core_contract = [
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
for module_id, component_name, parent_id in core_contract:
    parent_handle = handles[parent_id] if parent_id else root
    location = local_delta(module_id, parent_id) if parent_id else tuple(source_modules[module_id]["assembly_location_cm"])
    handle, _component = add_mesh(core, parent_handle, module_id, component_name, location)
    handles[module_id] = handle
    components.append({"component": component_name, "module_id": module_id, "parent": parent_id or "DefaultSceneRoot", "relative_location_cm": list(location)})
mount_handle, mount = add_component(core, handles["changer_body"], unreal.SceneComponent, "ToolMount")
set_relative(mount, (0.0, 0.0, 0.0))
components.append({"component": "ToolMount", "module_id": None, "parent": "changer_body", "relative_location_cm": [0, 0, 0]})
equipped_handle, equipped = add_component(core, mount_handle, unreal.ChildActorComponent, "EquippedTool")
band_bp = lib.load_asset(TOOL_ROOT + "/BP_LB_RobotTool_BandCutterCapture_v005")
equipped.set_editor_property("child_actor_class", bp_lib.generated_class(band_bp))
set_relative(equipped, (0.0, 0.0, 0.0))
components.append({
    "component": "EquippedTool", "module_id": "BandCutterCapture",
    "parent": "ToolMount", "relative_location_cm": [0, 0, 0],
    "replaceable_child_actor_class": True,
})
carrier_handle, carrier = add_component(core, handles["j3"], unreal.StaticMeshComponent, "CairnwellPlateCarrier")
carrier.set_static_mesh(lib.load_asset("/Engine/BasicShapes/Cube.Cube"))
set_relative(carrier, (52.0, -49.8, 8.0))
carrier.set_editor_property("relative_scale3d", unreal.Vector(0.44, 0.006, 0.17))
carrier.set_material(0, plate_material)
components.append({
    "component": "CairnwellPlateCarrier", "module_id": None, "parent": "j3",
    "relative_location_cm": [52.0, -49.8, 8.0], "dimensions_cm": [44.0, 0.6, 17.0],
    "replaceable_branding_component": True,
})
logo_handle, logo = add_component(core, handles["j3"], unreal.StaticMeshComponent, "RobotAssetPlateFace")
logo.set_static_mesh(lib.load_asset("/Engine/BasicShapes/Plane.Plane"))
set_relative(logo, (52.0, -50.45, 8.0), (90.0, 0.0, 0.0))
logo.set_editor_property("relative_scale3d", unreal.Vector(0.42, 0.1575, 1.0))
logo.set_material(0, lib.load_asset("/Game/LineBoss/Brand/Cairnwell/Candidate_v002/M_Cairnwell_PrimaryLogo_Masked_v002"))
components.append({
    "component": "RobotAssetPlateFace", "module_id": None, "parent": "j3",
    "relative_location_cm": [52.0, -50.45, 8.0], "dimensions_cm": [42.0, 15.75],
    "replaceable_material_per_instance": True,
})
variable_specs = [
    ("StationId", "string"), ("EquipmentId", "string"),
    ("ConditionAgeYears", "float"), ("ConditionSeed", "int"),
    ("CurrentToolId", "string"),
    ("J1Degrees", "float"), ("J2Degrees", "float"), ("J3Degrees", "float"),
    ("J4Degrees", "float"), ("J5Degrees", "float"), ("J6Degrees", "float"),
    ("Enabled", "bool"), ("ToolLocked", "bool"), ("FaultCode", "string"),
    ("OperatingHours", "float"), ("ServiceCycles", "int"),
]
variables = []
for variable_name, basic_type in variable_specs:
    pin_type = bp_lib.get_basic_type_by_name(basic_type)
    if not bp_lib.add_member_variable(core, variable_name, pin_type):
        raise RuntimeError(f"Could not add reusable instance variable {variable_name}:{basic_type}")
    bp_lib.set_blueprint_variable_instance_editable(core, variable_name, True)
    variables.append({"name": variable_name, "type": basic_type, "instance_editable": True})
bp_lib.compile_blueprint(core)
if not lib.save_loaded_asset(core, only_if_is_dirty=False):
    raise RuntimeError(f"Could not save {core_path}")

payload = {
    "$schema": "line-boss/audit/reusable-modular-robot-blueprints-v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "REUSABLE_BLUEPRINT_COMPONENT_CANDIDATES_BUILT__PLACEMENT_RUNTIME_VISUAL_GATES_OPEN__NOT_PROMOTED",
    "contract": str(CONTRACT.relative_to(ROOT)).replace("\\", "/"),
    "robot_core": {"asset": core_path, "components": components},
    "instance_variables": variables,
    "tools": tools,
    "source_mesh_count": len(mesh_paths),
    "core_component_count": len(components),
    "tool_component_count": sum(len(tool["components"]) for tool in tools),
    "reuse_scope": "400 kg / 350 cm six-axis process cells using the documented quick-changer interface",
    "geometry_modified": False,
    "open_gates": [
        "place core and selected tool as a reusable test instance",
        "expose per-instance station, condition, pose, tool and fault parameters",
        "implement tool swap controller and presence/lock interlocks",
        "implement joint animation and documented limits",
        "replace complex-as-simple collision with release collision",
        "run swept collision, save/load and fresh fixed-camera visual gates"
    ],
    "promotion_authorized": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_REUSABLE_MODULAR_ROBOT_BLUEPRINTS_V001_PASS core={len(components)} tools={len(tools)} audit={AUDIT}")
unreal.SystemLibrary.quit_editor()
