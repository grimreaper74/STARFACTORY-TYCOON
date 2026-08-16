"""Persist and rebind only the generated RP01 v001 candidate dependencies.

The original build process duplicated 47 meshes and seven materials in memory
but did not save those duplicated packages before saving the Blueprint.  A
fresh-process audit correctly exposed the missing dependencies.  This repair
uses the existing build audit as the exact allow-list, creates no new scope,
deletes nothing, and leaves all source candidates untouched.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BUILD_AUDIT = ROOT / "Saved/Audits/lb_rp01_mobile_base_candidate_v001_build.json"
REPAIR_AUDIT = ROOT / "Saved/Audits/lb_rp01_mobile_base_candidate_v001_persist_repair.json"
BP_PATH = "/Game/LineBoss/Robots/Shared/RP01/Candidate_v001/Blueprints/BP_LB_RP01_MobileBase"
MAP_PATH = "/Game/LineBoss/Developer/Validation/LB_RP01_MobileBase_Candidate_v001"

asset_library = unreal.EditorAssetLibrary
bp_library = unreal.BlueprintEditorLibrary
subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
data_library = unreal.SubobjectDataBlueprintFunctionLibrary

if not BUILD_AUDIT.exists():
    raise RuntimeError(f"Missing exact repair allow-list {BUILD_AUDIT}")
build = json.loads(BUILD_AUDIT.read_text(encoding="utf-8"))
if build.get("blueprint") != BP_PATH or build.get("validation_map") != MAP_PATH:
    raise RuntimeError("Build audit does not describe the exact generated v001 targets")
if len(build.get("duplicated_meshes", [])) != 47 or len(build.get("duplicated_materials", [])) != 7:
    raise RuntimeError("Build audit dependency counts are not the expected 47 meshes and seven materials")

persisted_materials = []
for row in build["duplicated_materials"]:
    source = row["source"]
    destination = row["candidate"]
    asset = unreal.load_asset(destination)
    if asset is None:
        if not asset_library.duplicate_asset(source, destination):
            raise RuntimeError(f"Could not recreate generated material {destination} from {source}")
        asset = unreal.load_asset(destination)
    if not isinstance(asset, unreal.MaterialInterface):
        raise RuntimeError(f"Generated material dependency has wrong class: {destination}")
    if not asset_library.save_loaded_asset(asset, only_if_is_dirty=False):
        raise RuntimeError(f"Could not persist generated material {destination}")
    persisted_materials.append(destination)

persisted_meshes = []
for row in build["duplicated_meshes"]:
    source = row["source"]
    destination = row["candidate"]
    asset = unreal.load_asset(destination)
    if asset is None:
        if not asset_library.duplicate_asset(source, destination):
            raise RuntimeError(f"Could not recreate generated mesh {destination} from {source}")
        asset = unreal.load_asset(destination)
    if not isinstance(asset, unreal.StaticMesh):
        raise RuntimeError(f"Generated mesh dependency has wrong class: {destination}")
    if not asset_library.save_loaded_asset(asset, only_if_is_dirty=False):
        raise RuntimeError(f"Could not persist generated mesh {destination}")
    persisted_meshes.append(destination)

blueprint = unreal.load_asset(BP_PATH)
if not isinstance(blueprint, unreal.Blueprint):
    raise RuntimeError(f"Missing generated Blueprint {BP_PATH}")

def normalize_component_name(name):
    if name.endswith("_GEN_VARIABLE"):
        return name[: -len("_GEN_VARIABLE")]
    return name


templates = {}
for handle in subsystem.k2_gather_subobject_data_for_blueprint(blueprint):
    data = subsystem.k2_find_subobject_data_from_handle(handle)
    component = data_library.get_object_for_blueprint(data, blueprint)
    if component is None:
        component = data_library.get_object(data)
    if component is not None:
        templates[normalize_component_name(component.get_name())] = component

rebound = []
for row in build["components"]:
    if row.get("role") != "temporary_shared_visual":
        continue
    component = templates.get(row["component"])
    if not isinstance(component, unreal.StaticMeshComponent):
        raise RuntimeError(f"Missing generated visual component template {row['component']}")
    mesh = unreal.load_asset(row["mesh"])
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"Missing persisted candidate mesh {row['mesh']}")
    component.set_static_mesh(mesh)
    material_rows = []
    for override in row.get("canonical_material_overrides", []):
        material = unreal.load_asset(override["canonical"])
        if not isinstance(material, unreal.MaterialInterface):
            raise RuntimeError(f"Missing persisted candidate material {override['canonical']}")
        component.set_material(int(override["slot"]), material)
        material_rows.append(override["canonical"])
    rebound.append({"component": row["component"], "mesh": row["mesh"], "materials": material_rows})

if len(rebound) != 47:
    raise RuntimeError(f"Expected to rebind 47 visual templates, rebound {len(rebound)}")
bp_library.compile_blueprint(blueprint)
if not asset_library.save_loaded_asset(blueprint, only_if_is_dirty=False):
    raise RuntimeError(f"Could not save rebound Blueprint {BP_PATH}")

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not levels.load_level(MAP_PATH):
    raise RuntimeError(f"Could not reload generated validation map {MAP_PATH}")
if not levels.save_current_level():
    raise RuntimeError(f"Could not resave generated validation map {MAP_PATH}")

payload = {
    "$schema": "line-boss/audit/lb-rp01-mobile-base-candidate-v001-persist-repair/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "GENERATED_DEPENDENCIES_PERSISTED_AND_BLUEPRINT_REBOUND__INDEPENDENT_AUDIT_REQUIRED__NOT_PROMOTED",
    "root_cause": "EditorAssetLibrary.duplicate_asset products were not explicitly saved before the original process exited",
    "blueprint": BP_PATH,
    "validation_map": MAP_PATH,
    "persisted_material_count": len(persisted_materials),
    "persisted_mesh_count": len(persisted_meshes),
    "rebound_visual_count": len(rebound),
    "rebound_visuals": rebound,
    "source_assets_modified": False,
    "deleted_assets": [],
    "runtime_ai_implemented": False,
    "savegame_binding_implemented": False,
    "promotion_authorized": False,
}
REPAIR_AUDIT.parent.mkdir(parents=True, exist_ok=True)
REPAIR_AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(
    f"LINE_BOSS_RP01_MOBILE_BASE_CANDIDATE_V001_PERSIST_REPAIR_PASS "
    f"meshes={len(persisted_meshes)} materials={len(persisted_materials)} visuals={len(rebound)} audit={REPAIR_AUDIT}"
)
unreal.SystemLibrary.quit_editor()
