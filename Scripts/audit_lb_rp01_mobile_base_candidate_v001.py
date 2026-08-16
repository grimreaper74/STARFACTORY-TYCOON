"""Independent fresh-process audit for BP_LB_RP01_MobileBase candidate v001."""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
CANDIDATE_ROOT = "/Game/LineBoss/Robots/Shared/RP01/Candidate_v001"
MESH_ROOT = CANDIDATE_ROOT + "/Meshes"
MATERIAL_ROOT = CANDIDATE_ROOT + "/Materials"
BP_PATH = CANDIDATE_ROOT + "/Blueprints/BP_LB_RP01_MobileBase"
MAP_PATH = "/Game/LineBoss/Developer/Validation/LB_RP01_MobileBase_Candidate_v001"
BUILD_AUDIT = ROOT / "Saved/Audits/lb_rp01_mobile_base_candidate_v001_build.json"
OUT = ROOT / "Saved/Audits/lb_rp01_mobile_base_candidate_v001_independent.json"

asset_library = unreal.EditorAssetLibrary
bp_library = unreal.BlueprintEditorLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

EXPECTED_VARIABLES = {
    "PlatformModelId": ("string", "LB-RP01"),
    "RobotUniqueId": ("string", "RP01-UNASSIGNED"),
    "PayloadVariant": ("string", "BASE"),
    "BatteryChargePercent": ("real", 100.0),
    "BatteryHealthPercent": ("real", 100.0),
    "BatteryCapacityAh": ("real", 105.0),
    "ConditionState": ("string", "RESTORED"),
    "ConditionAgeYears": ("real", 0.0),
    "ConditionSeed": ("int", 0),
    "FaultCode": ("string", ""),
    "FaultLatched": ("bool", False),
    "CurrentRouteId": ("string", ""),
    "RouteProgress01": ("real", 0.0),
    "CurrentDockId": ("string", ""),
    "DockState": ("string", "UNDOCKED"),
    "IsDocked": ("bool", False),
    "IsEnabled": ("bool", False),
    "OperatingHours": ("real", 0.0),
    "ServiceCycles": ("int", 0),
}

EXPECTED_ANCHORS = {
    "PayloadInterface": ("DefaultSceneRoot", (0.0, 0.0, 38.5)),
    "Attach_CR01_Payload": ("PayloadInterface", (0.0, 0.0, 0.0)),
    "Attach_MR01_Payload": ("PayloadInterface", (0.0, 0.0, 0.0)),
    "Attach_ConfigSpecificService": ("PayloadInterface", (0.0, 0.0, 0.0)),
    "Attach_DriveWheel_L": ("DefaultSceneRoot", (-10.0, -40.5, 17.0)),
    "Attach_DriveWheel_R": ("DefaultSceneRoot", (-10.0, 40.5, 17.0)),
    "Attach_Suspension_Front": ("DefaultSceneRoot", (47.0, 0.0, 16.0)),
    "Attach_CasterRoll_Front": ("Attach_Suspension_Front", (0.0, 0.0, -8.0)),
    "Attach_Suspension_Rear": ("DefaultSceneRoot", (-53.0, 0.0, 16.0)),
    "Attach_CasterRoll_Rear": ("Attach_Suspension_Rear", (0.0, 0.0, -8.0)),
    "Attach_Sensor_Front": ("DefaultSceneRoot", (66.0, 0.0, 50.0)),
    "Attach_Sensor_Rear": ("DefaultSceneRoot", (-66.0, 0.0, 50.0)),
    "Attach_Sensor_Left": ("DefaultSceneRoot", (0.0, -41.0, 50.0)),
    "Attach_Sensor_Right": ("DefaultSceneRoot", (0.0, 41.0, 50.0)),
    "Attach_DockDatum": ("DefaultSceneRoot", (-73.5, 0.0, 31.0)),
    "Attach_ChargeContact_L": ("DefaultSceneRoot", (-73.5, -12.0, 34.0)),
    "Attach_ChargeContact_R": ("DefaultSceneRoot", (-73.5, 12.0, 34.0)),
    "Attach_NetworkContact": ("DefaultSceneRoot", (-73.5, 0.0, 39.0)),
    "Attach_TowFront": ("DefaultSceneRoot", (73.5, 0.0, 18.0)),
    "Attach_TowRear": ("DefaultSceneRoot", (-73.5, 0.0, 18.0)),
    "Attach_AudioDrive_L": ("DefaultSceneRoot", (-10.0, -40.5, 17.0)),
    "Attach_AudioDrive_R": ("DefaultSceneRoot", (-10.0, 40.5, 17.0)),
    "Attach_AudioWarning": ("DefaultSceneRoot", (-62.0, 0.0, 85.0)),
}


def normalize_component_name(name):
    for suffix in ("_GEN_VARIABLE", "_0"):
        if name.endswith(suffix):
            name = name[: -len(suffix)]
    return name


def close_vec(actual, expected, tolerance=0.01):
    return all(abs(a - e) <= tolerance for a, e in zip(actual, expected))


def pin_description(pin):
    try:
        category = str(pin.get_editor_property("pin_category"))
    except Exception:
        category = ""
    try:
        subcategory = str(pin.get_editor_property("pin_sub_category"))
    except Exception:
        subcategory = ""
    try:
        exported = pin.export_text()
    except Exception:
        exported = str(pin)
    if not category:
        match = re.search(r'PinCategory="([^"]*)"', exported)
        category = match.group(1) if match else ""
    if not subcategory:
        match = re.search(r'PinSubCategory="([^"]*)"', exported)
        subcategory = match.group(1) if match else ""
    return {"category": category, "subcategory": subcategory, "export_text": exported}


failures = []
if not BUILD_AUDIT.exists():
    failures.append(f"Missing build audit {BUILD_AUDIT}")
build = json.loads(BUILD_AUDIT.read_text(encoding="utf-8")) if BUILD_AUDIT.exists() else {}

blueprint = unreal.load_asset(BP_PATH)
if not isinstance(blueprint, unreal.Blueprint):
    failures.append(f"Missing Blueprint {BP_PATH}")
    raise RuntimeError(failures[-1])
bp_library.compile_blueprint(blueprint)
blueprint_status = str(blueprint.get_editor_property("status"))
if "ERROR" in blueprint_status.upper():
    failures.append(f"Blueprint compile status {blueprint_status}")

generated_class = bp_library.generated_class(blueprint)
default_object = unreal.get_default_object(generated_class) if generated_class else None
if default_object is None or not isinstance(default_object, unreal.Pawn):
    failures.append("Generated class is not a Pawn")

member_names = {str(name) for name in bp_library.list_member_variable_names(blueprint, False)}
missing_variables = sorted(set(EXPECTED_VARIABLES) - member_names)
unexpected_variables = sorted(member_names - set(EXPECTED_VARIABLES))
if missing_variables:
    failures.append(f"Missing variables: {missing_variables}")
if unexpected_variables:
    failures.append(f"Unexpected variables: {unexpected_variables}")

variable_rows = []
default_mismatches = []
type_mismatches = []
for name, (expected_category, expected_default) in EXPECTED_VARIABLES.items():
    if name not in member_names:
        continue
    pin = bp_library.get_member_variable_type(blueprint, name)
    description = pin_description(pin)
    category = description["category"].lower()
    if category != expected_category:
        type_mismatches.append({"name": name, "expected": expected_category, "actual": description})
    actual_default = default_object.get_editor_property(name)
    default_ok = actual_default == expected_default
    if isinstance(expected_default, float):
        default_ok = isinstance(actual_default, float) and abs(actual_default - expected_default) <= 1e-6
    elif isinstance(expected_default, bool):
        default_ok = type(actual_default) is bool and actual_default == expected_default
    elif isinstance(expected_default, int):
        default_ok = type(actual_default) is int and actual_default == expected_default
    if not default_ok:
        default_mismatches.append({"name": name, "expected": expected_default, "actual": actual_default, "python_type": str(type(actual_default))})
    variable_rows.append({
        "name": name,
        "pin": description,
        "default": actual_default,
        "python_type": str(type(actual_default)),
    })
if type_mismatches:
    failures.append(f"Variable pin mismatches: {type_mismatches}")
if default_mismatches:
    failures.append(f"Default mismatches: {default_mismatches}")

mesh_paths = [
    path for path in asset_library.list_assets(MESH_ROOT, recursive=False, include_folder=False)
    if isinstance(unreal.load_asset(path), unreal.StaticMesh)
]
material_paths = [
    path for path in asset_library.list_assets(MATERIAL_ROOT, recursive=False, include_folder=False)
    if isinstance(unreal.load_asset(path), unreal.MaterialInterface)
]
if len(mesh_paths) != 47:
    failures.append(f"Expected 47 isolated meshes, found {len(mesh_paths)}")
if len(material_paths) != 7:
    failures.append(f"Expected 7 isolated materials, found {len(material_paths)}")

if not levels.load_level(MAP_PATH):
    failures.append(f"Could not load validation map {MAP_PATH}")
    raise RuntimeError(failures[-1])
instances = [actor for actor in actors.get_all_level_actors() if actor.get_actor_label() == "LB_RP01_MobileBase_Candidate_v001"]
if len(instances) != 1:
    failures.append(f"Expected one validation instance, found {len(instances)}")
    raise RuntimeError(failures[-1])
robot = instances[0]
if not isinstance(robot, unreal.Pawn):
    failures.append("Validation instance is not a Pawn")

scene_components = robot.get_components_by_class(unreal.SceneComponent)
component_by_name = {normalize_component_name(component.get_name()): component for component in scene_components}
root_components = [component for component in scene_components if component.get_attach_parent() is None]
root_names = [normalize_component_name(component.get_name()) for component in root_components]
if len(root_components) != 1 or root_names != ["DefaultSceneRoot"]:
    failures.append(f"Expected sole DefaultSceneRoot, got {root_names}")

anchor_rows = []
anchor_mismatches = []
for name, (expected_parent, expected_location) in EXPECTED_ANCHORS.items():
    component = component_by_name.get(name)
    if component is None:
        anchor_mismatches.append({"component": name, "problem": "missing"})
        continue
    parent = component.get_attach_parent()
    parent_name = normalize_component_name(parent.get_name()) if parent else None
    location = tuple(component.get_editor_property("relative_location").to_tuple())
    row = {"component": name, "parent": parent_name, "relative_location_cm": list(location)}
    anchor_rows.append(row)
    if parent_name != expected_parent or not close_vec(location, expected_location):
        row["expected_parent"] = expected_parent
        row["expected_location_cm"] = list(expected_location)
        anchor_mismatches.append(row)
if anchor_mismatches:
    failures.append(f"Anchor hierarchy/transform mismatches: {anchor_mismatches}")

alignment = component_by_name.get("VisualAlignment_v032")
alignment_rotation = None
if alignment is None:
    failures.append("Missing VisualAlignment_v032")
else:
    rotation = alignment.get_editor_property("relative_rotation")
    alignment_rotation = [rotation.roll, rotation.pitch, rotation.yaw]
    parent = alignment.get_attach_parent()
    if normalize_component_name(parent.get_name()) != "DefaultSceneRoot" or abs(abs(rotation.yaw) - 180.0) > 0.01:
        failures.append(f"Visual alignment correction mismatch: parent={parent.get_name()} rotation={alignment_rotation}")

visual_components = [
    component for component in robot.get_components_by_class(unreal.StaticMeshComponent)
    if normalize_component_name(component.get_name()).startswith("Visual_")
]
visual_rows = []
external_effective_materials = []
invalid_mesh_bindings = []
simple_collision_total = 0
for component in visual_components:
    mesh = component.get_editor_property("static_mesh")
    mesh_path = mesh.get_path_name() if mesh else None
    if not mesh_path or not mesh_path.startswith(MESH_ROOT + "/"):
        invalid_mesh_bindings.append({"component": component.get_name(), "mesh": mesh_path})
    effective_materials = []
    for index in range(component.get_num_materials()):
        material = component.get_material(index)
        material_path = material.get_path_name() if material else None
        effective_materials.append(material_path)
        if material_path and not material_path.startswith(MATERIAL_ROOT + "/"):
            external_effective_materials.append({"component": component.get_name(), "slot": index, "material": material_path})
    collision = {"box": 0, "sphere": 0, "capsule": 0, "convex": 0}
    if mesh:
        try:
            body_setup = mesh.get_editor_property("body_setup")
            aggregate = body_setup.get_editor_property("agg_geom") if body_setup else None
            if aggregate:
                collision = {
                    "box": len(aggregate.get_editor_property("box_elems")),
                    "sphere": len(aggregate.get_editor_property("sphere_elems")),
                    "capsule": len(aggregate.get_editor_property("sphyl_elems")),
                    "convex": len(aggregate.get_editor_property("convex_elems")),
                }
        except Exception:
            pass
    simple_collision_total += sum(collision.values())
    parent = component.get_attach_parent()
    visual_rows.append({
        "component": normalize_component_name(component.get_name()),
        "parent": normalize_component_name(parent.get_name()) if parent else None,
        "mesh": mesh_path,
        "effective_materials": effective_materials,
        "simple_collision": collision,
    })
if len(visual_components) != 47:
    failures.append(f"Expected 47 visual components, found {len(visual_components)}")
if invalid_mesh_bindings:
    failures.append(f"Visuals reference non-candidate meshes: {invalid_mesh_bindings}")
if external_effective_materials:
    failures.append(f"Visuals have non-canonical effective materials: {external_effective_materials}")

expected_instance = build.get("validation_state", {})
instance_state = {}
instance_mismatches = []
for name, expected in expected_instance.items():
    actual = robot.get_editor_property(name)
    instance_state[name] = actual
    if actual != expected:
        instance_mismatches.append({"name": name, "expected": expected, "actual": actual})
if instance_mismatches:
    failures.append(f"Reloaded validation state mismatch: {instance_mismatches}")

payload = {
    "$schema": "line-boss/audit/lb-rp01-mobile-base-candidate-v001-independent/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "TECHNICAL_ARCHITECTURE_GATE_PASS__RUNTIME_SAVE_COLLISION_VISUAL_GATES_OPEN__NOT_PROMOTED" if not failures else "TECHNICAL_ARCHITECTURE_GATE_FAIL__NOT_PROMOTED",
    "blueprint": BP_PATH,
    "blueprint_status": blueprint_status,
    "generated_class_is_pawn": isinstance(default_object, unreal.Pawn),
    "validation_map": MAP_PATH,
    "validation_actor": robot.get_actor_label(),
    "root_component_count": len(root_components),
    "root_components": root_names,
    "member_variable_count": len(member_names),
    "variables": variable_rows,
    "missing_variables": missing_variables,
    "unexpected_variables": unexpected_variables,
    "type_mismatches": type_mismatches,
    "default_mismatches": default_mismatches,
    "instance_state": instance_state,
    "instance_mismatches": instance_mismatches,
    "anchor_count": len(anchor_rows),
    "anchors": anchor_rows,
    "anchor_mismatches": anchor_mismatches,
    "visual_alignment_rotation_deg": alignment_rotation,
    "candidate_mesh_asset_count": len(mesh_paths),
    "candidate_material_asset_count": len(material_paths),
    "visual_component_count": len(visual_components),
    "visuals": visual_rows,
    "invalid_mesh_bindings": invalid_mesh_bindings,
    "external_effective_materials": external_effective_materials,
    "simple_collision_primitive_total": simple_collision_total,
    "collision_gate": "OPEN__NO_RELEASE_COLLISION_ASSERTED",
    "runtime_ai_gate": "OPEN__NO_MOVEMENT_OR_ROUTE_CONTROLLER_IMPLEMENTED",
    "docking_runtime_gate": "OPEN__DATA_AND_ANCHORS_ONLY",
    "savegame_gate": "OPEN__NO_SAVEGAME_BINDING_IMPLEMENTED",
    "fresh_fixed_camera_visual_gate": "OPEN",
    "source_assets_modified": False,
    "failures": failures,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
if failures:
    unreal.log_error(f"LINE_BOSS_RP01_MOBILE_BASE_CANDIDATE_V001_AUDIT_FAIL failures={len(failures)} audit={OUT}")
    raise RuntimeError("; ".join(failures))
unreal.log(
    f"LINE_BOSS_RP01_MOBILE_BASE_CANDIDATE_V001_AUDIT_PASS "
    f"roots={len(root_components)} anchors={len(anchor_rows)} visuals={len(visual_components)} "
    f"variables={len(member_names)} audit={OUT}"
)
unreal.SystemLibrary.quit_editor()
