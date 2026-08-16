"""Build finer-scale shared paint, RP01 v003, and CR01 v054 without overwrites."""

from datetime import datetime, timezone
import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE_MATERIAL_ROOT = "/Game/LineBoss/Robots/Shared/Materials/Candidate_v002"
MATERIAL_ROOT = "/Game/LineBoss/Robots/Shared/Materials/Candidate_v003"
SOURCE_PARENT_BP = "/Game/LineBoss/Robots/Shared/RP01/Candidate_v002/Blueprints/BP_LB_RP01_MobileBase"
PARENT_BP = "/Game/LineBoss/Robots/Shared/RP01/Candidate_v003/Blueprints/BP_LB_RP01_MobileBase"
SOURCE_CR_BP = "/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v053/Blueprints/BP_LB_CR01_CleaningAMR_v053"
CR_BP = "/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v054/Blueprints/BP_LB_CR01_CleaningAMR_v054"
AUDIT = ROOT / "Saved/Audits/lb_cr01_candidate_v054_release_materials_build.json"

assets = unreal.EditorAssetLibrary
bp_library = unreal.BlueprintEditorLibrary
subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
data_library = unreal.SubobjectDataBlueprintFunctionLibrary
mat_library = unreal.MaterialEditingLibrary


def require(path, cls=None):
    asset = assets.load_asset(path)
    if asset is None or (cls is not None and not isinstance(asset, cls)):
        raise RuntimeError(f"Missing required asset {path}")
    return asset


for path in (MATERIAL_ROOT, "/Game/LineBoss/Robots/Shared/RP01/Candidate_v003", "/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v054"):
    if assets.does_directory_exist(path):
        raise RuntimeError(f"Refusing to overwrite preserved candidate namespace {path}")


def duplicate_mi(semantic, condition, source_semantic=None):
    source_semantic = source_semantic or semantic
    src = f"{SOURCE_MATERIAL_ROOT}/MI_LB_Robot_{source_semantic}_{condition}_v002"
    dst = f"{MATERIAL_ROOT}/MI_LB_Robot_{semantic}_{condition}_v003"
    if not assets.duplicate_asset(src, dst):
        raise RuntimeError(f"Could not duplicate {src} -> {dst}")
    return require(dst, unreal.MaterialInstanceConstant)


palette = {
    "BodyCharcoal": {
        "Restored": unreal.LinearColor(0.030, 0.038, 0.046, 1.0),
        "Mothballed": unreal.LinearColor(0.021, 0.027, 0.032, 1.0),
    },
    "SafetyYellow": {
        "Restored": unreal.LinearColor(0.72, 0.36, 0.006, 1.0),
        "Mothballed": unreal.LinearColor(0.48, 0.225, 0.006, 1.0),
    },
    "CairnwellGreen": {
        "Restored": unreal.LinearColor(0.012, 0.095, 0.071, 1.0),
        "Mothballed": unreal.LinearColor(0.010, 0.052, 0.043, 1.0),
    },
    "ServiceGrey": {
        "Restored": unreal.LinearColor(0.095, 0.115, 0.125, 1.0),
        "Mothballed": unreal.LinearColor(0.060, 0.070, 0.074, 1.0),
    },
    "MarkingWarmWhite": {
        "Restored": unreal.LinearColor(0.74, 0.69, 0.58, 1.0),
        "Mothballed": unreal.LinearColor(0.30, 0.275, 0.225, 1.0),
    },
}

material_rows = []
material_assets = {}
for semantic in palette:
    for condition in ("Restored", "Mothballed"):
        source_semantic = "ServiceGrey" if semantic == "MarkingWarmWhite" else semantic
        material = duplicate_mi(semantic, condition, source_semantic)
        is_moth = condition == "Mothballed"
        scalars = {
            "TextureScale": 18.0,
            "WearContrast": 2.15 if is_moth else 2.45,
            "PaintCoverageBias": 0.78 if is_moth else 0.93,
            "DustAmount": 0.24 if is_moth else 0.035,
            "NormalStrength": 0.055,
            "BaseRoughness": 0.69 if is_moth else 0.53,
            "RoughnessVariation": 0.10,
            "DustRoughness": 0.84,
            "ExposedMetallic": 0.68,
        }
        for name, value in scalars.items():
            mat_library.set_material_instance_scalar_parameter_value(material, name, value)
        mat_library.set_material_instance_vector_parameter_value(material, "PaintColour", palette[semantic][condition])
        if not assets.save_loaded_asset(material, only_if_is_dirty=False):
            raise RuntimeError(f"Could not save {material.get_path_name()}")
        material_assets[f"{semantic}_{condition}"] = material
        material_rows.append({
            "semantic": semantic,
            "condition": condition,
            "asset": material.get_path_name(),
            "scalars": scalars,
            "paint_colour_linear": list(palette[semantic][condition].to_tuple()),
        })


def component_objects(blueprint):
    result = {}
    for handle in subsystem.k2_gather_subobject_data_for_blueprint(blueprint):
        data = subsystem.k2_find_subobject_data_from_handle(handle)
        name = str(data_library.get_variable_name(data))
        obj = data_library.get_object_for_blueprint(data, blueprint) or data_library.get_object(data)
        if name and name != "None" and name not in result:
            result[name] = obj
    return result


if not assets.duplicate_asset(SOURCE_PARENT_BP, PARENT_BP):
    raise RuntimeError("Could not duplicate corrected RP01 v002 to v003")
parent = require(PARENT_BP, unreal.Blueprint)
parent_bindings = []
for name, component in sorted(component_objects(parent).items()):
    if not name.startswith("Visual_") or not isinstance(component, unreal.StaticMeshComponent):
        continue
    mesh = component.get_editor_property("static_mesh")
    if mesh is None:
        continue
    for index, slot in enumerate(mesh.get_editor_property("static_materials")):
        slot_name = str(slot.get_editor_property("material_slot_name"))
        material = None
        role = None
        if "BodyCharcoal" in slot_name or "FrameAnthracite" in slot_name:
            material, role = material_assets["BodyCharcoal_Mothballed"], "fine_charcoal"
        elif "SafetyYellow" in slot_name:
            material, role = material_assets["SafetyYellow_Mothballed"], "restrained_safety_yellow"
        elif "BrushedSteel" in slot_name and any(token in name for token in ("DriveRim", "CasterRim", "CasterFork")):
            material, role = material_assets["ServiceGrey_Mothballed"], "dark_running_gear_service_metal"
        if material is not None:
            component.set_material(index, material)
            parent_bindings.append({"component": name, "slot": index, "slot_name": slot_name, "material": material.get_path_name(), "role": role})

bp_library.compile_blueprint(parent)
parent_class = bp_library.generated_class(parent)
if parent_class is None:
    raise RuntimeError("RP01 v003 generated class missing")
unreal.get_default_object(parent_class).set_editor_property("tags", [
    unreal.Name("LB.SupportRobot.Platform.LB-RP01"),
    unreal.Name("LB.Asset.Candidate.v003"),
    unreal.Name("LB.Asset.CandidateNotPromoted"),
    unreal.Name("LB.RP01.VisualAnchorCorrection"),
    unreal.Name("LB.RP01.FineScalePaint"),
])
bp_library.compile_blueprint(parent)
if not assets.save_loaded_asset(parent, only_if_is_dirty=False):
    raise RuntimeError("Could not save RP01 v003")

if not assets.duplicate_asset(SOURCE_CR_BP, CR_BP):
    raise RuntimeError("Could not duplicate CR01 v053 to v054")
cleaner = require(CR_BP, unreal.Blueprint)
bp_library.reparent_blueprint(cleaner, parent_class)

cleaner_bindings = []
for name, component in sorted(component_objects(cleaner).items()):
    if not isinstance(component, unreal.StaticMeshComponent):
        continue
    mesh = component.get_editor_property("static_mesh")
    if mesh is None or not mesh.get_path_name().startswith("/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v052/Meshes/"):
        continue
    for index, slot in enumerate(mesh.get_editor_property("static_materials")):
        slot_name = str(slot.get_editor_property("material_slot_name"))
        material = None
        role = None
        if any(token in slot_name for token in ("BodyCharcoal", "FrameAnthracite", "GraphitePowdercoat")):
            material, role = material_assets["BodyCharcoal_Mothballed"], "fine_charcoal"
        elif any(token in slot_name for token in ("SafetyYellow", "FunctionSafetyYellow", "CairnwellSafetyYellow")):
            material, role = material_assets["SafetyYellow_Mothballed"], "restrained_safety_yellow"
        elif any(token in slot_name for token in ("CairnwellGreen", "RuggedGreen")):
            material, role = material_assets["CairnwellGreen_Mothballed"], "cairnwell_green"
        elif "CairnwellWarmWhite" in slot_name:
            material, role = material_assets["MarkingWarmWhite_Mothballed"], "legible_warm_white_marking"
        elif "HopperPolymer" in slot_name:
            material, role = material_assets["ServiceGrey_Mothballed"], "service_grey"
        if material is not None:
            component.set_material(index, material)
            cleaner_bindings.append({"component": name, "slot": index, "slot_name": slot_name, "material": material.get_path_name(), "role": role})

bp_library.compile_blueprint(cleaner)
cleaner_class = bp_library.generated_class(cleaner)
if cleaner_class is None:
    raise RuntimeError("CR01 v054 generated class missing")
unreal.get_default_object(cleaner_class).set_editor_property("tags", [
    unreal.Name("LB.SupportRobot.LB-CR01"),
    unreal.Name("LB.Asset.Candidate.v054"),
    unreal.Name("LB.Asset.CandidateNotPromoted"),
    unreal.Name("LB.RP01.ParentCandidate.v003"),
    unreal.Name("LB.Brand.CairnwellAutomotive"),
    unreal.Name("LB.Site.MoorcrossWorks"),
    unreal.Name("LB.Safety.FaultLatched"),
])
bp_library.compile_blueprint(cleaner)
if not assets.save_loaded_asset(cleaner, only_if_is_dirty=False):
    raise RuntimeError("Could not save CR01 v054")

result = {
    "$schema": "line-boss/audit/lb-cr01-candidate-v054-release-materials-build",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "FINE_SCALE_LAYERED_PAINT_AND_CORRECTED_RUNNING_GEAR_BUILT__FRESH_RELOAD_AND_CAMERA_GATES_REQUIRED__NOT_PROMOTED",
    "source_material_root_preserved": SOURCE_MATERIAL_ROOT,
    "material_root": MATERIAL_ROOT,
    "material_instances_created": len(material_rows),
    "materials": material_rows,
    "source_parent_preserved": SOURCE_PARENT_BP,
    "parent_blueprint": PARENT_BP,
    "parent_material_binding_count": len(parent_bindings),
    "parent_material_bindings": parent_bindings,
    "source_cleaner_preserved": SOURCE_CR_BP,
    "cleaner_blueprint": CR_BP,
    "cleaner_material_binding_count": len(cleaner_bindings),
    "cleaner_material_bindings": cleaner_bindings,
    "branding_contract": ["Cairnwell Automotive", "Moorcross Works"],
    "line_boss_in_world_branding_added": False,
    "geometry_modified": False,
    "collision_components_inherited": True,
    "promotion_authorized": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
unreal.log(f"LINE_BOSS_CR01_V054_RELEASE_MATERIAL_BUILD_PASS materials={len(material_rows)} parent_bindings={len(parent_bindings)} cleaner_bindings={len(cleaner_bindings)} audit={AUDIT}")
