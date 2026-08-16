"""Compose CR01 v059 with RP01 v003 and the approved layered material set."""

from datetime import datetime, timezone
import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE_BP = "/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v059/Blueprints/BP_LB_CR01_CleaningAMR_v059"
PARENT_BP = "/Game/LineBoss/Robots/Shared/RP01/Candidate_v003/Blueprints/BP_LB_RP01_MobileBase"
BP_PATH = "/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v060/Blueprints/BP_LB_CR01_CleaningAMR_v060"
AUDIT = ROOT / "Saved/Audits/lb_cr01_candidate_v060_scrubber_visual_build.json"
PAINT_ROOT = "/Game/LineBoss/Robots/Shared/Materials/Candidate_v003"
PAYLOAD_ROOT = "/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v059/Meshes/"
RP01_ROOT = "/Game/LineBoss/Robots/Shared/RP01/"

assets = unreal.EditorAssetLibrary
blueprints = unreal.BlueprintEditorLibrary
subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
data_library = unreal.SubobjectDataBlueprintFunctionLibrary


def require(path, cls=None):
    asset = assets.load_asset(path)
    if asset is None or (cls is not None and not isinstance(asset, cls)):
        raise RuntimeError(f"Missing required asset {path}")
    return asset


if assets.does_directory_exist("/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v060"):
    raise RuntimeError("Refusing to overwrite preserved CR01 Candidate v060")

source = require(SOURCE_BP, unreal.Blueprint)
parent = require(PARENT_BP, unreal.Blueprint)
parent_class = blueprints.generated_class(parent)
if parent_class is None:
    raise RuntimeError("Corrected RP01 v003 generated class is unavailable")
if not assets.duplicate_asset(SOURCE_BP, BP_PATH):
    raise RuntimeError(f"Could not duplicate {SOURCE_BP} -> {BP_PATH}")
blueprint = require(BP_PATH, unreal.Blueprint)
blueprints.reparent_blueprint(blueprint, parent_class)

paint = {
    semantic: require(f"{PAINT_ROOT}/MI_LB_Robot_{semantic}_Mothballed_v003", unreal.MaterialInterface)
    for semantic in ("BodyCharcoal", "SafetyYellow", "CairnwellGreen", "ServiceGrey", "MarkingWarmWhite")
}


def material_for(slot_name):
    if any(token in slot_name for token in ("BodyCharcoal", "FrameAnthracite", "GraphitePowdercoat")):
        return paint["BodyCharcoal"], "layered_body_charcoal"
    if any(token in slot_name for token in ("SafetyYellow", "FunctionSafetyYellow", "CairnwellSafetyYellow")):
        return paint["SafetyYellow"], "restrained_safety_yellow"
    if any(token in slot_name for token in ("CairnwellGreen", "RuggedGreen")):
        return paint["CairnwellGreen"], "cairnwell_identity_green"
    if "CairnwellWarmWhite" in slot_name:
        return paint["MarkingWarmWhite"], "warm_white_diegetic_marking"
    if any(token in slot_name for token in ("BrushedSteel", "CarrierSteel", "WearSteel", "HopperPolymer", "DarkServiceMetal")):
        return paint["ServiceGrey"], "dark_service_metal"
    return None, None


rows = []
seen = set()
for handle in subsystem.k2_gather_subobject_data_for_blueprint(blueprint):
    data = subsystem.k2_find_subobject_data_from_handle(handle)
    name = str(data_library.get_variable_name(data))
    component = data_library.get_object_for_blueprint(data, blueprint) or data_library.get_object(data)
    if not isinstance(component, unreal.StaticMeshComponent):
        continue
    mesh = component.get_editor_property("static_mesh")
    if mesh is None:
        continue
    mesh_path = mesh.get_path_name()
    if not (mesh_path.startswith(PAYLOAD_ROOT) or mesh_path.startswith(RP01_ROOT)):
        continue
    for index, slot in enumerate(mesh.get_editor_property("static_materials")):
        key = (name, index)
        if key in seen:
            continue
        slot_name = str(slot.get_editor_property("material_slot_name"))
        material, role = material_for(slot_name)
        if material is None:
            continue
        component.set_material(index, material)
        rows.append({
            "component": name,
            "mesh": mesh_path,
            "slot": index,
            "slot_name": slot_name,
            "material": material.get_path_name(),
            "role": role,
        })
        seen.add(key)

blueprints.compile_blueprint(blueprint)
generated_class = blueprints.generated_class(blueprint)
if generated_class is None:
    raise RuntimeError("CR01 v060 generated class is unavailable")
unreal.get_default_object(generated_class).set_editor_property("tags", [
    unreal.Name("LB.SupportRobot.LB-CR01"),
    unreal.Name("LB.Asset.Candidate.v060"),
    unreal.Name("LB.Asset.CandidateNotPromoted"),
    unreal.Name("LB.RP01.ParentCandidate.v003"),
    unreal.Name("LB.Brand.CairnwellAutomotive"),
    unreal.Name("LB.Site.MoorcrossWorks"),
    unreal.Name("LB.CR01.ScrubberSilhouette.v059"),
    unreal.Name("LB.CR01.LightSupportStatesOnly"),
])
blueprints.compile_blueprint(blueprint)
if not assets.save_loaded_asset(blueprint, only_if_is_dirty=False):
    raise RuntimeError(f"Could not save {BP_PATH}")

AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps({
    "$schema": "line-boss/audit/lb-cr01-candidate-v060-scrubber-visual-build",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "ROUNDED_SCRUBBER_VISUAL_AND_LAYERED_MATERIALS_BUILT__FRESH_UNREAL_CAMERA_GATES_REQUIRED__NOT_PROMOTED",
    "source_blueprint_preserved": SOURCE_BP,
    "corrected_parent_blueprint": PARENT_BP,
    "candidate_blueprint": BP_PATH,
    "payload_mesh_namespace": PAYLOAD_ROOT,
    "material_binding_count": len(rows),
    "material_bindings": rows,
    "branding_contract": ["Cairnwell Automotive", "CR-01 001", "Moorcross Works"],
    "line_boss_in_world_branding_added": False,
    "fault_scope": "LIGHT_PLAYER_READABLE_SUPPORT_STATES_ONLY",
    "geometry_modified_in_unreal": False,
    "promotion_authorized": False,
}, indent=2) + "\n", encoding="utf-8")
unreal.log(f"LINE_BOSS_CR01_V060_SCRUBBER_VISUAL_BUILD_PASS bindings={len(rows)} audit={AUDIT}")
