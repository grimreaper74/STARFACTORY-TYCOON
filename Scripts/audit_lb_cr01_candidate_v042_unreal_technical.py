"""Fresh-process technical audit for the quarantined CR01 v042 child Pawn."""

from datetime import datetime, timezone
import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
CONTRACT_PATH = ROOT / "SourceAssets/Robots/LB_CR01_CleaningAMR/Data/LB_CR01_UNREAL_CHILD_COMPOSITION_CONTRACT_v001.json"
BUILD_AUDIT = ROOT / "Saved/Audits/lb_cr01_candidate_v042_unreal_technical_build.json"
OUT = ROOT / "Saved/Audits/lb_cr01_candidate_v042_unreal_technical_independent.json"
PARENT_BP_PATH = "/Game/LineBoss/Robots/Shared/RP01/Candidate_v001/Blueprints/BP_LB_RP01_MobileBase"
CANDIDATE_ROOT = "/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v042"
MESH_ROOT = CANDIDATE_ROOT + "/Meshes"
BP_PATH = CANDIDATE_ROOT + "/Blueprints/BP_LB_CR01_CleaningAMR_v042"
RP_MESH_ROOT = "/Game/LineBoss/Robots/Shared/RP01/Candidate_v001/Meshes"

asset_library = unreal.EditorAssetLibrary
bp_library = unreal.BlueprintEditorLibrary
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def normalize(name):
    value = str(name)
    for suffix in ("_GEN_VARIABLE", "_0"):
        if value.endswith(suffix):
            value = value[:-len(suffix)]
    return value


def close_vec(actual, expected, tolerance=0.02):
    return all(abs(a - e) <= tolerance for a, e in zip(actual, expected))


def collision_count(mesh):
    try:
        body_setup = mesh.get_editor_property("body_setup")
        aggregate = body_setup.get_editor_property("agg_geom") if body_setup else None
        if aggregate is None:
            return 0
        return sum(len(aggregate.get_editor_property(name)) for name in (
            "box_elems", "sphere_elems", "sphyl_elems", "convex_elems"
        ))
    except Exception:
        return 0


failures = []
if not CONTRACT_PATH.is_file() or not BUILD_AUDIT.is_file():
    raise RuntimeError("Missing composition contract or v042 build audit")
contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
build = json.loads(BUILD_AUDIT.read_text(encoding="utf-8"))

parent_blueprint = asset_library.load_asset(PARENT_BP_PATH)
blueprint = asset_library.load_asset(BP_PATH)
if not isinstance(parent_blueprint, unreal.Blueprint) or not isinstance(blueprint, unreal.Blueprint):
    raise RuntimeError("Missing RP01 parent or CR01 child Blueprint")
bp_library.compile_blueprint(blueprint)
blueprint_status = str(blueprint.get_editor_property("status"))
if "ERROR" in blueprint_status.upper():
    failures.append(f"Blueprint status is {blueprint_status}")

parent_class = bp_library.generated_class(parent_blueprint)
generated_class = bp_library.generated_class(blueprint)
default_object = unreal.get_default_object(generated_class) if generated_class else None
if default_object is None or not isinstance(default_object, unreal.Pawn):
    failures.append("Generated class is not a Pawn")
# UE 5.8's Python Blueprint wrapper does not expose ParentClass/SuperClass.
# The inheritance gate below therefore uses the reloaded parent's canonical
# anchors and all 47 RP01 visual bindings on the child CDO as concrete proof.

robot = actors_api.spawn_actor_from_class(generated_class, unreal.Vector(0.0, 0.0, 0.0), unreal.Rotator())
if robot is None:
    raise RuntimeError("Could not spawn disposable CR01 audit instance")
robot.set_actor_label("LB_CR01_v042_DisposableTechnicalAudit")
scene_components = robot.get_components_by_class(unreal.SceneComponent)
components = {normalize(component.get_name()): component for component in scene_components}
roots = [component for component in scene_components if component.get_attach_parent() is None]
root_names = [normalize(component.get_name()) for component in roots]
if root_names != ["DefaultSceneRoot"]:
    failures.append(f"Expected sole DefaultSceneRoot, got {root_names}")

hierarchy_rows = []
hierarchy_mismatches = []
frame = components.get("CR01PayloadFrame")
if frame is None:
    hierarchy_mismatches.append({"component": "CR01PayloadFrame", "problem": "missing"})
else:
    parent = frame.get_attach_parent()
    location = tuple(frame.get_editor_property("relative_location").to_tuple())
    if normalize(parent.get_name()) != "Attach_CR01_Payload" or not close_vec(location, (0.0, 0.0, -38.5)):
        hierarchy_mismatches.append({
            "component": "CR01PayloadFrame", "parent": normalize(parent.get_name()),
            "relative_location_cm": list(location),
        })

for stage in contract["cr01_child_hierarchy"]:
    component = components.get(stage["component"])
    expected_parent = "CR01PayloadFrame" if stage["parent"] == "DefaultSceneRoot" else stage["parent"]
    if component is None:
        hierarchy_mismatches.append({"component": stage["component"], "stage_id": stage["id"], "problem": "missing"})
        continue
    parent = component.get_attach_parent()
    parent_name = normalize(parent.get_name()) if parent else None
    location = tuple(component.get_editor_property("relative_location").to_tuple())
    row = {
        "component": stage["component"],
        "stage_id": stage["id"],
        "parent": parent_name,
        "relative_location_cm": list(location),
        "class": component.get_class().get_name(),
    }
    hierarchy_rows.append(row)
    if parent_name != expected_parent or not close_vec(location, tuple(stage["location_cm"])):
        row["expected_parent"] = expected_parent
        row["expected_location_cm"] = stage["location_cm"]
        hierarchy_mismatches.append(row)
    expects_mesh = stage["role"] not in {"carrier", "required_source_geometry"}
    is_mesh = isinstance(component, unreal.StaticMeshComponent)
    if is_mesh != expects_mesh:
        hierarchy_mismatches.append({
            "component": stage["component"], "stage_id": stage["id"],
            "expected_mesh_component": expects_mesh, "actual_class": component.get_class().get_name(),
        })
    if is_mesh:
        mesh = component.get_editor_property("static_mesh")
        path = mesh.get_path_name() if mesh else None
        row["mesh"] = path
        if not path or not path.startswith(MESH_ROOT + "/"):
            hierarchy_mismatches.append({"component": stage["component"], "invalid_mesh": path})

if hierarchy_mismatches:
    failures.append(f"Child hierarchy/type/transform mismatches: {hierarchy_mismatches}")

mesh_paths = [
    path for path in asset_library.list_assets(MESH_ROOT, recursive=False, include_folder=False)
    if isinstance(asset_library.load_asset(path), unreal.StaticMesh)
]
if len(mesh_paths) != 20:
    failures.append(f"Expected 20 imported StaticMeshes, found {len(mesh_paths)}")
shared_name_leaks = [path for path in mesh_paths if "RP01" in Path(path).name.upper()]
if shared_name_leaks:
    failures.append(f"Candidate import contains RP01-named shared meshes: {shared_name_leaks}")

mesh_rows = []
simple_collision_total = 0
for path in sorted(mesh_paths):
    mesh = asset_library.load_asset(path)
    box = mesh.get_bounding_box()
    size = box.max - box.min
    count = collision_count(mesh)
    simple_collision_total += count
    mesh_rows.append({
        "asset": path,
        "bounds_size_cm": list(size.to_tuple()),
        "simple_collision_primitive_count": count,
        "material_slots": [
            str(slot.get_editor_property("material_slot_name"))
            for slot in mesh.get_editor_property("static_materials")
        ],
    })

payload_path = MESH_ROOT + "/SM_LB_CR01_PayloadUpperStatic_XForwardCM_v042"
payload_mesh = asset_library.load_asset(payload_path)
if not isinstance(payload_mesh, unreal.StaticMesh):
    failures.append("Missing imported payload upper static mesh")
    payload_size = None
else:
    box = payload_mesh.get_bounding_box()
    payload_size = tuple((box.max - box.min).to_tuple())
    if not close_vec(payload_size, (150.3, 98.464, 79.7), tolerance=0.08):
        failures.append(f"Payload bounds/scale mismatch: {payload_size}")

safe_defaults = build["safe_campaign_defaults"]
default_rows = []
for name, expected in safe_defaults.items():
    actual = default_object.get_editor_property(name)
    default_rows.append({"name": name, "expected": expected, "actual": actual})
    matches = actual == expected
    if isinstance(expected, float):
        matches = isinstance(actual, float) and abs(actual - expected) <= 1e-6
    if not matches:
        failures.append(f"Safe default mismatch {name}: {actual!r} != {expected!r}")

condition_rows = []
for name, expected_visible in (
    ("Condition_Mothballed_Root", True),
    ("Condition_Restored_Root", False),
    ("Condition_Mothballed_SqueegeeYaw", True),
    ("Condition_Restored_SqueegeeYaw", False),
):
    component = components.get(name)
    if not isinstance(component, unreal.StaticMeshComponent):
        failures.append(f"Missing condition component {name}")
        continue
    visible = bool(component.get_editor_property("visible"))
    hidden_in_game = bool(component.get_editor_property("hidden_in_game"))
    condition_rows.append({"component": name, "visible": visible, "hidden_in_game": hidden_in_game})
    if visible != expected_visible or hidden_in_game == expected_visible:
        failures.append(f"Condition visibility mismatch {name}: visible={visible} hidden={hidden_in_game}")

parent_visuals = []
material_binding_rows = []
default_material_bindings = []
shared_paint_binding_count = 0
for component in robot.get_components_by_class(unreal.StaticMeshComponent):
    mesh = component.get_editor_property("static_mesh")
    path = mesh.get_path_name() if mesh else None
    if path and path.startswith(RP_MESH_ROOT + "/"):
        parent_visuals.append(path)
    if path and path.startswith(MESH_ROOT + "/"):
        for index in range(component.get_num_materials()):
            material = component.get_material(index)
            material_path = material.get_path_name() if material else None
            row = {
                "component": normalize(component.get_name()),
                "mesh": path,
                "slot": index,
                "material": material_path,
            }
            material_binding_rows.append(row)
            if not material_path or "DefaultMaterial" in material_path:
                default_material_bindings.append(row)
            if material_path and material_path.startswith("/Game/LineBoss/Robots/Shared/Materials/Candidate_v002/"):
                shared_paint_binding_count += 1
if len(parent_visuals) != 47:
    failures.append(f"Expected 47 inherited RP01 visual bindings, found {len(parent_visuals)}")
if len(material_binding_rows) != 58:
    failures.append(f"Expected 58 CR01 effective material bindings, found {len(material_binding_rows)}")
if shared_paint_binding_count != 28:
    failures.append(f"Expected 28 shared-paint v002 bindings, found {shared_paint_binding_count}")
if default_material_bindings:
    failures.append(f"CR01 components still use default materials: {default_material_bindings}")

result = {
    "$schema": "line-boss/audit/lb-cr01-candidate-v042-unreal-technical-independent",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "FRESH_RELOAD_TECHNICAL_COMPOSITION_PASS__VISUAL_RUNTIME_STOW_COLLISION_GATES_OPEN__NOT_PROMOTED" if not failures else "FRESH_RELOAD_TECHNICAL_COMPOSITION_FAIL__NOT_PROMOTED",
    "blueprint": BP_PATH,
    "parent_blueprint": PARENT_BP_PATH,
    "blueprint_status": blueprint_status,
    "generated_class_is_pawn": isinstance(default_object, unreal.Pawn),
    "root_components": root_names,
    "scene_component_count_including_inherited": len(scene_components),
    "inherited_rp01_visual_count": len(parent_visuals),
    "child_stage_count": len(hierarchy_rows),
    "child_hierarchy": hierarchy_rows,
    "hierarchy_mismatches": hierarchy_mismatches,
    "imported_static_mesh_count": len(mesh_paths),
    "shared_mesh_name_leaks": shared_name_leaks,
    "payload_bounds_size_cm": list(payload_size) if payload_size else None,
    "meshes": mesh_rows,
    "simple_collision_primitive_total": simple_collision_total,
    "safe_defaults": default_rows,
    "condition_components": condition_rows,
    "effective_material_binding_count": len(material_binding_rows),
    "shared_paint_v002_binding_count": shared_paint_binding_count,
    "effective_material_bindings": material_binding_rows,
    "default_material_bindings": default_material_bindings,
    "stow_gate": "FAIL__PUBLISHED_RANGE_ONLY_REACHES_1252.6377_MM",
    "rotational_swept_cleaning_gate": "OPEN",
    "material_binding_gate": "OPEN",
    "runtime_navigation_docking_save_gate": "OPEN",
    "fresh_fixed_camera_pro_comparison_gate": "OPEN",
    "failures": failures,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
actors_api.destroy_actor(robot)
if failures:
    unreal.log_error(f"LINE_BOSS_CR01_V042_TECHNICAL_AUDIT_FAIL failures={len(failures)} audit={OUT}")
    raise RuntimeError("; ".join(failures))
unreal.log(
    f"LINE_BOSS_CR01_V042_TECHNICAL_AUDIT_PASS meshes={len(mesh_paths)} "
    f"stages={len(hierarchy_rows)} inherited_visuals={len(parent_visuals)} audit={OUT}"
)
unreal.SystemLibrary.quit_editor()
