"""Import and assemble quarantined CR01 Candidate v042 as an RP01 child.

This is a technical composition candidate only.  It intentionally has no
release collision, navigation/runtime registration, map placement or promotion.
The published side-brush stow conflict remains fault-latched and explicit.
"""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = ROOT / "SourceAssets/Robots/LB_CR01_CleaningAMR/Exports/Candidate_v042_PayloadRig"
EXPORT_AUDIT = ROOT / "SourceAssets/Robots/LB_CR01_CleaningAMR/Validation/Candidate_v042/LB_CR01_ExportReimportAudit_v042.json"
CONTRACT_PATH = ROOT / "SourceAssets/Robots/LB_CR01_CleaningAMR/Data/LB_CR01_UNREAL_CHILD_COMPOSITION_CONTRACT_v001.json"
PARENT_BP_PATH = "/Game/LineBoss/Robots/Shared/RP01/Candidate_v001/Blueprints/BP_LB_RP01_MobileBase"
CANDIDATE_ROOT = "/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v042"
MESH_ROOT = CANDIDATE_ROOT + "/Meshes"
BP_PATH = CANDIDATE_ROOT + "/Blueprints/BP_LB_CR01_CleaningAMR_v042"
AUDIT_PATH = ROOT / "Saved/Audits/lb_cr01_candidate_v042_unreal_technical_build.json"

asset_library = unreal.EditorAssetLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
bp_library = unreal.BlueprintEditorLibrary
subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
data_library = unreal.SubobjectDataBlueprintFunctionLibrary


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def require_asset(path: str, cls=None):
    asset = unreal.load_asset(path)
    if asset is None:
        raise RuntimeError(f"Missing required asset {path}")
    if cls is not None and not isinstance(asset, cls):
        raise RuntimeError(f"Unexpected class for {path}: {asset.get_class().get_name()}")
    return asset


def gather_unique_handles(blueprint):
    result = {}
    for handle in subsystem.k2_gather_subobject_data_for_blueprint(blueprint):
        data = subsystem.k2_find_subobject_data_from_handle(handle)
        name = str(data_library.get_variable_name(data))
        if name and name != "None" and name not in result:
            result[name] = handle
    return result


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
        raise RuntimeError(f"Could not add component {name}: {failure}")
    subsystem.rename_subobject(handle=handle, new_name=unreal.Text(name))
    data = subsystem.k2_find_subobject_data_from_handle(handle)
    component = data_library.get_object_for_blueprint(data, blueprint) or data_library.get_object(data)
    if component is None:
        raise RuntimeError(f"Could not resolve component template {name}")
    return handle, component


def set_relative(component, location, rotation=(0.0, 0.0, 0.0)):
    component.set_editor_property("relative_location", unreal.Vector(*location))
    component.set_editor_property("relative_rotation", unreal.Rotator(*rotation))
    component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)


if not SOURCE.is_dir() or not EXPORT_AUDIT.is_file() or not CONTRACT_PATH.is_file():
    raise RuntimeError("Missing v042 export, export audit or composition contract")
if asset_library.does_directory_exist(CANDIDATE_ROOT) or asset_library.does_asset_exist(BP_PATH):
    raise RuntimeError(f"Refusing to overwrite preserved Unreal candidate {CANDIDATE_ROOT}")

export_audit = json.loads(EXPORT_AUDIT.read_text(encoding="utf-8"))
contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
if export_audit.get("fbx_count") != 24 or len(export_audit.get("files", [])) != 24:
    raise RuntimeError("v042 export audit does not contain the required 24 FBXs")
if contract.get("parent_blueprint") != PARENT_BP_PATH:
    raise RuntimeError("Composition contract parent Blueprint changed")

source_rows = []
for row in export_audit["files"]:
    path = SOURCE / Path(row["file"]).name
    if not path.is_file():
        raise RuntimeError(f"Missing audited FBX {path}")
    actual_hash = sha256(path)
    if actual_hash != row["sha256"]:
        raise RuntimeError(f"FBX hash mismatch for {path.name}: {actual_hash} != {row['sha256']}")
    source_rows.append({
        "file": path,
        "sha256": actual_hash,
        "source_status": row["status"],
        "stage_id": row.get("stage_id"),
    })

tasks = []
for row in source_rows:
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(row["file"]),
        "destination_path": MESH_ROOT,
        "automated": True,
        "replace_existing": False,
        "save": True,
    })
    options = unreal.FbxImportUI()
    options.set_editor_properties({
        "import_mesh": True,
        "import_as_skeletal": False,
        "import_materials": False,
        "import_textures": False,
        "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
    })
    options.get_editor_property("static_mesh_import_data").set_editor_properties({
        "combine_meshes": True,
        "convert_scene": True,
        "convert_scene_unit": True,
        "force_front_x_axis": False,
        "transform_vertex_to_absolute": False,
        "import_uniform_scale": 1.0,
        "generate_lightmap_u_vs": True,
        "auto_generate_collision": False,
        "remove_degenerates": True,
    })
    task.set_editor_property("options", options)
    tasks.append(task)

asset_tools.import_asset_tasks(tasks)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
mesh_paths = [
    path for path in asset_library.list_assets(MESH_ROOT, recursive=False, include_folder=False)
    if isinstance(unreal.load_asset(path), unreal.StaticMesh)
]
meshes = {unreal.load_asset(path).get_name(): unreal.load_asset(path) for path in mesh_paths}
expected_mesh_names = sorted(Path(row["file"]).stem for row in export_audit["files"] if row["status"] == "PASS_MESH")
missing_meshes = sorted(set(expected_mesh_names) - set(meshes))
unexpected_meshes = sorted(set(meshes) - set(expected_mesh_names))
if len(meshes) != 20 or missing_meshes or unexpected_meshes:
    raise RuntimeError(
        f"Imported mesh inventory mismatch count={len(meshes)} missing={missing_meshes} unexpected={unexpected_meshes}"
    )

parent_blueprint = require_asset(PARENT_BP_PATH, unreal.Blueprint)
parent_class = bp_library.generated_class(parent_blueprint)
if parent_class is None:
    raise RuntimeError("RP01 parent generated class is missing")
blueprint = bp_library.create_blueprint_asset_with_parent(BP_PATH, parent_class)
if not isinstance(blueprint, unreal.Blueprint):
    raise RuntimeError(f"Could not create child Blueprint {BP_PATH}")

handles = gather_unique_handles(blueprint)
parent_anchor = handles.get("Attach_CR01_Payload")
if parent_anchor is None:
    raise RuntimeError("Child Blueprint did not expose inherited Attach_CR01_Payload")

payload_root_handle, payload_root = add_component(blueprint, parent_anchor, unreal.SceneComponent, "CR01PayloadFrame")
# Parent anchor is at +38.5 cm; this cancels it so all contract transforms stay
# in the RP01 CFR root frame without introducing a second root component.
set_relative(payload_root, (0.0, 0.0, -38.5))
payload_root.set_editor_property("component_tags", [
    unreal.Name("LB.CR01.PayloadFrame"), unreal.Name("LB.Asset.CandidateNotPromoted")
])

component_rows = [{
    "component": "CR01PayloadFrame",
    "parent": "Attach_CR01_Payload",
    "relative_location_cm": [0.0, 0.0, -38.5],
    "net_root_location_cm": [0.0, 0.0, 0.0],
    "role": "variant_frame_not_root",
}]

payload_mesh_name = "SM_LB_CR01_PayloadUpperStatic_XForwardCM_v042"
payload_handle, payload_visual = add_component(
    blueprint, payload_root_handle, unreal.StaticMeshComponent, "Visual_CR01_PayloadUpperStatic"
)
payload_visual.set_static_mesh(meshes[payload_mesh_name])
set_relative(payload_visual, (0.0, 0.0, 0.0))
payload_visual.set_editor_property("component_tags", [
    unreal.Name("LB.CR01.Payload.Static"), unreal.Name("LB.Asset.CandidateNotPromoted")
])
component_rows.append({
    "component": "Visual_CR01_PayloadUpperStatic",
    "parent": "CR01PayloadFrame",
    "mesh": meshes[payload_mesh_name].get_path_name(),
    "role": "cr01_only_static_payload",
})

stage_mesh_names = {
    row["stage_id"]: Path(row["file"]).stem
    for row in source_rows
    if row["stage_id"] and row["source_status"] == "PASS_MESH"
}
stage_handles = {}
for stage in contract["cr01_child_hierarchy"]:
    stage_id = stage["id"]
    parent_name = stage["parent"]
    parent_handle = payload_root_handle if parent_name == "DefaultSceneRoot" else stage_handles.get(
        next((candidate["id"] for candidate in contract["cr01_child_hierarchy"] if candidate["component"] == parent_name), "")
    )
    if parent_handle is None:
        raise RuntimeError(f"Missing parent handle {parent_name} for {stage_id}")
    mesh_name = stage_mesh_names.get(stage_id)
    component_class = unreal.StaticMeshComponent if mesh_name else unreal.SceneComponent
    handle, component = add_component(blueprint, parent_handle, component_class, stage["component"])
    set_relative(component, tuple(stage["location_cm"]))
    tags = [unreal.Name(f"LB.CR01.Stage.{stage_id}"), unreal.Name("LB.Asset.CandidateNotPromoted")]
    role = "mesh"
    mesh_path = None
    if mesh_name:
        mesh = meshes[mesh_name]
        component.set_static_mesh(mesh)
        mesh_path = mesh.get_path_name()
    else:
        role = "required_missing_source_geometry" if stage["role"] == "required_source_geometry" else "explicit_carrier"
        tags.append(unreal.Name("LB.CR01.MissingSourceGeometry") if role.startswith("required") else unreal.Name("LB.CR01.Carrier"))
    component.set_editor_property("component_tags", tags)
    stage_handles[stage_id] = handle
    component_rows.append({
        "component": stage["component"],
        "stage_id": stage_id,
        "parent": parent_name if parent_name != "DefaultSceneRoot" else "CR01PayloadFrame",
        "relative_location_cm": stage["location_cm"],
        "role": role,
        "mesh": mesh_path,
    })

condition_specs = [
    ("Condition_Mothballed_Root", "SM_LB_CR01_Condition_Mothballed_Root_XForwardCM_v042", payload_root_handle, True),
    ("Condition_Restored_Root", "SM_LB_CR01_Condition_Restored_Root_XForwardCM_v042", payload_root_handle, False),
    ("Condition_Mothballed_SqueegeeYaw", "SM_LB_CR01_Condition_Mothballed_SqueegeeYaw_XForwardCM_v042", stage_handles["M19"], True),
    ("Condition_Restored_SqueegeeYaw", "SM_LB_CR01_Condition_Restored_SqueegeeYaw_XForwardCM_v042", stage_handles["M19"], False),
]
for name, mesh_name, parent_handle, visible in condition_specs:
    _handle, component = add_component(blueprint, parent_handle, unreal.StaticMeshComponent, name)
    component.set_static_mesh(meshes[mesh_name])
    set_relative(component, (0.0, 0.0, 0.0))
    component.set_editor_property("visible", visible)
    component.set_editor_property("hidden_in_game", not visible)
    component.set_editor_property("component_tags", [
        unreal.Name("LB.CR01.Condition.Mothballed" if "Mothballed" in name else "LB.CR01.Condition.Restored"),
        unreal.Name("LB.Asset.CandidateNotPromoted"),
    ])
    component_rows.append({
        "component": name,
        "parent": "PVT_SqueegeeYaw" if "SqueegeeYaw" in name else "CR01PayloadFrame",
        "mesh": meshes[mesh_name].get_path_name(),
        "default_visible": visible,
        "role": "condition_overlay",
    })

for socket_name, location in contract["cr01_only_sockets_cm"].items():
    _handle, component = add_component(blueprint, payload_root_handle, unreal.SceneComponent, socket_name)
    set_relative(component, tuple(location))
    component.set_editor_property("component_tags", [
        unreal.Name(f"LB.CR01.Socket.{socket_name}"), unreal.Name("LB.Asset.CandidateNotPromoted")
    ])
    component_rows.append({
        "component": socket_name,
        "parent": "CR01PayloadFrame",
        "relative_location_cm": location,
        "role": "cr01_only_socket",
    })

bp_library.compile_blueprint(blueprint)
generated_class = bp_library.generated_class(blueprint)
if generated_class is None:
    raise RuntimeError("CR01 generated class is missing after compile")
default_object = unreal.get_default_object(generated_class)
safe_defaults = {
    "PlatformModelId": "LB-RP01",
    "RobotUniqueId": "CR01-UNASSIGNED",
    "PayloadVariant": "LB-CR01",
    "BatteryChargePercent": 0.0,
    "BatteryHealthPercent": 0.0,
    "ConditionState": "MOTHBALLED",
    "ConditionAgeYears": 7.0,
    "FaultCode": "RESTORATION_REQUIRED",
    "FaultLatched": True,
    "CurrentRouteId": "",
    "RouteProgress01": 0.0,
    "CurrentDockId": "",
    "DockState": "UNVERIFIED",
    "IsDocked": False,
    "IsEnabled": False,
    "OperatingHours": 0.0,
    "ServiceCycles": 0,
}
for name, value in safe_defaults.items():
    default_object.set_editor_property(name, value)
default_object.set_editor_property("tags", [
    unreal.Name("LB.SupportRobot.LB-CR01"),
    unreal.Name("LB.Asset.Candidate.v042"),
    unreal.Name("LB.Asset.CandidateNotPromoted"),
    unreal.Name("LB.Safety.FaultLatched"),
    unreal.Name("LB.CR01.StowConflictOpen"),
])
bp_library.compile_blueprint(blueprint)
if not asset_library.save_loaded_asset(blueprint, only_if_is_dirty=False):
    raise RuntimeError(f"Could not save {BP_PATH}")
asset_library.save_directory(MESH_ROOT, only_if_is_dirty=False, recursive=False)

mesh_rows = []
for name, mesh in sorted(meshes.items()):
    box = mesh.get_bounding_box()
    size = box.max - box.min
    mesh_rows.append({
        "name": name,
        "asset": mesh.get_path_name(),
        "bounds_min_cm": list(box.min.to_tuple()),
        "bounds_max_cm": list(box.max.to_tuple()),
        "bounds_size_cm": list(size.to_tuple()),
    })

result = {
    "$schema": "line-boss/audit/lb-cr01-candidate-v042-unreal-technical-build",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "QUARANTINED_IMPORT_AND_CHILD_COMPOSITION_BUILT__FRESH_AUDIT_REQUIRED__NOT_PROMOTED",
    "source": str(SOURCE),
    "source_fbx_count": len(source_rows),
    "source_hashes_verified": True,
    "import_destination": MESH_ROOT,
    "imported_static_mesh_count": len(meshes),
    "declared_null_stage_ids": sorted(row["stage_id"] for row in source_rows if row["source_status"] == "PASS_DECLARED_NULL"),
    "meshes": mesh_rows,
    "parent_blueprint": PARENT_BP_PATH,
    "child_blueprint": BP_PATH,
    "child_component_count": len(component_rows),
    "components": component_rows,
    "safe_campaign_defaults": safe_defaults,
    "collision_policy": "NO_AUTOGENERATED_COLLISION__RELEASE_COLLISION_GATE_OPEN",
    "material_policy": "SOURCE_SLOT_NAMES_PRESERVED__SHARED_V002_BINDING_GATE_OPEN",
    "stow_gate": "FAIL__1252.6377_MM_AT_PUBLISHED_65_DEG_VS_980_PLUS_MINUS_5_MM",
    "swept_cleaning_gate": "OPEN__ANALYTIC_OR_FULL_ROTATION_UNREAL_PROOF_REQUIRED",
    "runtime_registration": False,
    "map_modified": False,
    "open_gates": [
        "fresh Blueprint compile/reload/hierarchy/default/bounds audit",
        "M20 debris-hopper and M25 filter-housing production geometry",
        "compliant carrier-contained side-brush stow mechanism",
        "shared material v002 semantic binding and robot-scale tuning",
        "simple collision and articulated swept-volume tests",
        "navigation, docking, service, fault and SaveGame runtime",
        "fresh fixed-camera Unreal comparison against the Pro reference"
    ],
    "promotion_authorized": False,
}
AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
AUDIT_PATH.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
unreal.log(
    f"LINE_BOSS_CR01_V042_TECHNICAL_BUILD_PASS meshes={len(meshes)} "
    f"components={len(component_rows)} audit={AUDIT_PATH}"
)
unreal.SystemLibrary.quit_editor()
