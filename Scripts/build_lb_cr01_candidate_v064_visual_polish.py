"""Build isolated CR01 v064 visual polish without modifying v063 or accepted maps."""

from datetime import datetime, timezone
import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE_MATERIAL_ROOT = "/Game/LineBoss/Robots/Shared/Materials/Candidate_v003"
MATERIAL_ROOT = "/Game/LineBoss/Robots/Shared/Materials/Candidate_v004"
SOURCE_BP = "/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v062/Blueprints/BP_LB_CR01_CleaningAMR_v062"
BP_PATH = "/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v064/Blueprints/BP_LB_CR01_CleaningAMR_v064"
AUDIT = ROOT / "Saved/Audits/lb_cr01_candidate_v064_visual_polish_build.json"

assets = unreal.EditorAssetLibrary
blueprints = unreal.BlueprintEditorLibrary
subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
data_library = unreal.SubobjectDataBlueprintFunctionLibrary
mat_library = unreal.MaterialEditingLibrary


def require(path, cls=None):
    asset = assets.load_asset(path)
    if asset is None or (cls is not None and not isinstance(asset, cls)):
        raise RuntimeError(f"Missing required asset {path}")
    return asset


for path in (MATERIAL_ROOT, "/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v064"):
    if assets.does_directory_exist(path):
        raise RuntimeError(f"Refusing to overwrite preserved candidate namespace {path}")

palette = {
    "BodyCharcoal": {
        "Restored": unreal.LinearColor(0.026, 0.034, 0.041, 1.0),
        "Mothballed": unreal.LinearColor(0.031, 0.030, 0.026, 1.0),
    },
    "SafetyYellow": {
        "Restored": unreal.LinearColor(0.68, 0.33, 0.005, 1.0),
        "Mothballed": unreal.LinearColor(0.34, 0.145, 0.004, 1.0),
    },
    "CairnwellGreen": {
        "Restored": unreal.LinearColor(0.010, 0.082, 0.061, 1.0),
        "Mothballed": unreal.LinearColor(0.018, 0.043, 0.035, 1.0),
    },
    "ServiceGrey": {
        "Restored": unreal.LinearColor(0.070, 0.085, 0.092, 1.0),
        "Mothballed": unreal.LinearColor(0.052, 0.049, 0.043, 1.0),
    },
    "MarkingWarmWhite": {
        "Restored": unreal.LinearColor(0.66, 0.62, 0.54, 1.0),
        "Mothballed": unreal.LinearColor(0.21, 0.19, 0.15, 1.0),
    },
}

materials = {}
material_rows = []
for semantic, conditions in palette.items():
    for condition, colour in conditions.items():
        src = f"{SOURCE_MATERIAL_ROOT}/MI_LB_Robot_{semantic}_{condition}_v003"
        dst = f"{MATERIAL_ROOT}/MI_LB_Robot_{semantic}_{condition}_v004"
        if not assets.duplicate_asset(src, dst):
            raise RuntimeError(f"Could not duplicate {src} -> {dst}")
        material = require(dst, unreal.MaterialInstanceConstant)
        moth = condition == "Mothballed"
        scalars = {
            "TextureScale": 18.0,
            "WearContrast": 2.85 if moth else 2.45,
            "PaintCoverageBias": 0.64 if moth else 0.93,
            "DustAmount": 0.43 if moth else 0.035,
            "NormalStrength": 0.065 if moth else 0.050,
            "BaseRoughness": 0.79 if moth else 0.52,
            "RoughnessVariation": 0.15 if moth else 0.09,
            "DustRoughness": 0.92 if moth else 0.84,
            "ExposedMetallic": 0.64,
        }
        for name, value in scalars.items():
            mat_library.set_material_instance_scalar_parameter_value(material, name, value)
        mat_library.set_material_instance_vector_parameter_value(material, "PaintColour", colour)
        if not assets.save_loaded_asset(material, only_if_is_dirty=False):
            raise RuntimeError(f"Could not save {dst}")
        materials[f"{semantic}_{condition}"] = material
        material_rows.append({"semantic": semantic, "condition": condition, "asset": dst, "scalars": scalars})

if not assets.duplicate_asset(SOURCE_BP, BP_PATH):
    raise RuntimeError(f"Could not duplicate {SOURCE_BP} -> {BP_PATH}")
blueprint = require(BP_PATH, unreal.Blueprint)


def material_for(slot_name):
    if any(token in slot_name for token in ("BodyCharcoal", "FrameAnthracite", "GraphitePowdercoat")):
        return materials["BodyCharcoal_Mothballed"], "dormant_body"
    if any(token in slot_name for token in ("SafetyYellow", "FunctionSafetyYellow", "CairnwellSafetyYellow")):
        return materials["SafetyYellow_Mothballed"], "dormant_safety_yellow"
    if any(token in slot_name for token in ("CairnwellGreen", "RuggedGreen")):
        return materials["CairnwellGreen_Mothballed"], "dormant_identity_green"
    if "CairnwellWarmWhite" in slot_name:
        return materials["MarkingWarmWhite_Mothballed"], "dormant_marking"
    if any(token in slot_name for token in ("BrushedSteel", "CarrierSteel", "WearSteel", "HopperPolymer", "DarkServiceMetal")):
        return materials["ServiceGrey_Mothballed"], "dormant_service_metal"
    return None, None


bindings = []
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
    if not (mesh_path.startswith("/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v059/Meshes/")
            or mesh_path.startswith("/Game/LineBoss/Robots/Shared/RP01/")):
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
        bindings.append({"component": name, "slot": index, "slot_name": slot_name, "material": material.get_path_name(), "role": role})
        seen.add(key)

blueprints.compile_blueprint(blueprint)
generated_class = blueprints.generated_class(blueprint)
if generated_class is None:
    raise RuntimeError("CR01 v064 generated class unavailable")
unreal.get_default_object(generated_class).set_editor_property("tags", [
    unreal.Name("LB.SupportRobot.LB-CR01"),
    unreal.Name("LB.Asset.Candidate.v064"),
    unreal.Name("LB.Asset.CandidateNotPromoted"),
    unreal.Name("LB.RP01.ParentCandidate.v003"),
    unreal.Name("LB.Brand.CairnwellAutomotive"),
    unreal.Name("LB.Site.MoorcrossWorks"),
    unreal.Name("LB.CR01.ScrubberSilhouette.v059"),
    unreal.Name("LB.CR01.DormantWear.v004"),
    unreal.Name("LB.CR01.LightSupportStatesOnly"),
])
blueprints.compile_blueprint(blueprint)
if not assets.save_loaded_asset(blueprint, only_if_is_dirty=False):
    raise RuntimeError(f"Could not save {BP_PATH}")

AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps({
    "$schema": "line-boss/audit/lb-cr01-candidate-v064-visual-polish-build",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "FOCUSED_DORMANT_WEAR_AND_UPPER_VALUE_POLISH_BUILT__FRESH_GATES_REQUIRED__NOT_PROMOTED",
    "source_blueprint_preserved": SOURCE_BP,
    "candidate_blueprint": BP_PATH,
    "source_material_root_preserved": SOURCE_MATERIAL_ROOT,
    "material_root": MATERIAL_ROOT,
    "material_instances_created": len(material_rows),
    "material_binding_count": len(bindings),
    "materials": material_rows,
    "material_bindings": bindings,
    "geometry_modified": False,
    "pivots_modified": False,
    "branding_contract": ["Cairnwell Automotive", "CR-01 001", "Moorcross Works"],
    "line_boss_in_world_branding_added": False,
    "fault_scope": "LIGHT_PLAYER_READABLE_SUPPORT_STATES_ONLY",
    "promotion_authorized": False
}, indent=2) + "\n", encoding="utf-8")
unreal.log(f"LINE_BOSS_CR01_V064_VISUAL_POLISH_PASS materials={len(material_rows)} bindings={len(bindings)} audit={AUDIT}")
