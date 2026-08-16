"""Separate CR01 marking colour from structural service metal/trim."""

from datetime import datetime, timezone
import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE_BP = "/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v055/Blueprints/BP_LB_CR01_CleaningAMR_v055"
BP_PATH = "/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v056/Blueprints/BP_LB_CR01_CleaningAMR_v056"
AUDIT = ROOT / "Saved/Audits/lb_cr01_candidate_v056_trim_hierarchy_build.json"
MESH_ROOT = "/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v052/Meshes/"

assets = unreal.EditorAssetLibrary
bp_library = unreal.BlueprintEditorLibrary
subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
data_library = unreal.SubobjectDataBlueprintFunctionLibrary


def require(path, cls=None):
    asset = assets.load_asset(path)
    if asset is None or (cls is not None and not isinstance(asset, cls)):
        raise RuntimeError(f"Missing required asset {path}")
    return asset


if assets.does_directory_exist("/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v056"):
    raise RuntimeError("Refusing to overwrite preserved CR01 Candidate v056")
if not assets.duplicate_asset(SOURCE_BP, BP_PATH):
    raise RuntimeError(f"Could not duplicate {SOURCE_BP} -> {BP_PATH}")
blueprint = require(BP_PATH, unreal.Blueprint)
service_grey = require(
    "/Game/LineBoss/Robots/Shared/Materials/Candidate_v003/MI_LB_Robot_ServiceGrey_Mothballed_v003",
    unreal.MaterialInterface,
)

rows = []
tokens = ("CairnwellWarmWhite", "BrushedSteel", "CarrierSteel", "BrushedServiceSteel", "WearSteel")
seen = set()
for handle in subsystem.k2_gather_subobject_data_for_blueprint(blueprint):
    data = subsystem.k2_find_subobject_data_from_handle(handle)
    name = str(data_library.get_variable_name(data))
    component = data_library.get_object_for_blueprint(data, blueprint) or data_library.get_object(data)
    if not isinstance(component, unreal.StaticMeshComponent):
        continue
    mesh = component.get_editor_property("static_mesh")
    if mesh is None or not mesh.get_path_name().startswith(MESH_ROOT):
        continue
    for index, slot in enumerate(mesh.get_editor_property("static_materials")):
        key = (name, index)
        if key in seen:
            continue
        slot_name = str(slot.get_editor_property("material_slot_name"))
        if not any(token in slot_name for token in tokens):
            continue
        component.set_material(index, service_grey)
        rows.append({
            "component": name,
            "mesh": mesh.get_path_name(),
            "slot": index,
            "slot_name": slot_name,
            "material": service_grey.get_path_name(),
            "role": "restrained_structural_service_trim",
        })
        seen.add(key)

if not rows:
    raise RuntimeError("No structural trim slots were separated")
bp_library.compile_blueprint(blueprint)
generated_class = bp_library.generated_class(blueprint)
if generated_class is None:
    raise RuntimeError("CR01 v056 generated class missing")
unreal.get_default_object(generated_class).set_editor_property("tags", [
    unreal.Name("LB.SupportRobot.LB-CR01"),
    unreal.Name("LB.Asset.Candidate.v056"),
    unreal.Name("LB.Asset.CandidateNotPromoted"),
    unreal.Name("LB.RP01.ParentCandidate.v003"),
    unreal.Name("LB.Brand.CairnwellAutomotive"),
    unreal.Name("LB.Site.MoorcrossWorks"),
    unreal.Name("LB.CR01.StructuralTrimSeparatedFromMarkings"),
])
bp_library.compile_blueprint(blueprint)
if not assets.save_loaded_asset(blueprint, only_if_is_dirty=False):
    raise RuntimeError(f"Could not save {BP_PATH}")

result = {
    "$schema": "line-boss/audit/lb-cr01-candidate-v056-trim-hierarchy-build",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "STRUCTURAL_TRIM_SEPARATED_FROM_DIEGETIC_MARKINGS__FRESH_RELOAD_AND_CAMERA_GATES_REQUIRED__NOT_PROMOTED",
    "source_blueprint_preserved": SOURCE_BP,
    "candidate_blueprint": BP_PATH,
    "binding_count": len(rows),
    "bindings": rows,
    "identity_components_inherited": True,
    "collision_components_inherited": True,
    "geometry_modified": False,
    "promotion_authorized": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
unreal.log(f"LINE_BOSS_CR01_V056_TRIM_HIERARCHY_BUILD_PASS bindings={len(rows)} audit={AUDIT}")
