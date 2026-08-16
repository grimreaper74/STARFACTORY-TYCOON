"""Apply restrained layered paint and believable steel overrides to PR-005 v044."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR005MaterialCandidate_v044"
ROOT = "/Game/LineBoss/Stations/Press/PR005/Candidate_v044/Materials"
SHARED_ROOT = "/Game/LineBoss/Shared/Materials/IndustrialPaint/Candidate_v044"
SOURCE_MASTER = "/Game/LineBoss/Equipment/Robots/Modular6Axis/Candidate_v020/Materials/M_LB_Robot_SurfaceForgePaint_Master_v020"
SHARED_MASTER = SHARED_ROOT + "/M_LB_Industrial_SurfaceForgePaint_Master_v044"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr005_material_candidate_v044.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
library = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
if not library.does_asset_exist(SHARED_MASTER):
    if not library.duplicate_asset(SOURCE_MASTER, SHARED_MASTER):
        raise RuntimeError("Could not duplicate the audited Surface Forge paint wrapper")


def instance(name, paint, exposed, scalars):
    path = ROOT + "/" + name
    asset = library.load_asset(path)
    if asset is None:
        asset = tools.create_asset(
            name, ROOT, unreal.MaterialInstanceConstant,
            unreal.MaterialInstanceConstantFactoryNew())
    if asset is None:
        raise RuntimeError(f"Could not create {path}")
    asset.set_editor_property("parent", library.load_asset(SHARED_MASTER))
    mel.set_material_instance_vector_parameter_value(asset, "PaintColour", unreal.LinearColor(*paint, 1.0))
    mel.set_material_instance_vector_parameter_value(asset, "ExposedMetalColour", unreal.LinearColor(*exposed, 1.0))
    for key, value in scalars.items():
        mel.set_material_instance_scalar_parameter_value(asset, key, value)
    mel.update_material_instance(asset)
    library.save_loaded_asset(asset, only_if_is_dirty=False)
    return asset


yellow = instance("MI_PR005_SafetyYellow_Layered_v044",
                  (0.72, 0.34, 0.020), (0.085, 0.078, 0.065), {
                      "TextureScale": 3.8, "PaintMaskContrast": 1.25,
                      "PaintCoverageBias": 0.98, "NormalStrength": 0.08,
                      "BaseRoughness": 0.52, "RoughnessVariation": 0.14,
                      "ExposedMetallic": 0.62,
                  })
dark = instance("MI_PR005_DarkMachine_Layered_v044",
                (0.022, 0.030, 0.034), (0.060, 0.066, 0.070), {
                    "TextureScale": 4.2, "PaintMaskContrast": 1.45,
                    "PaintCoverageBias": 0.95, "NormalStrength": 0.08,
                    "BaseRoughness": 0.58, "RoughnessVariation": 0.12,
                    "ExposedMetallic": 0.58,
                })


def simple_material(name, colour, metallic, roughness):
    path = ROOT + "/" + name
    asset = library.load_asset(path)
    if asset is None:
        asset = tools.create_asset(name, ROOT, unreal.Material, unreal.MaterialFactoryNew())
    if asset is None:
        raise RuntimeError(f"Could not create {path}")
    mel.delete_all_material_expressions(asset)
    base = mel.create_material_expression(asset, unreal.MaterialExpressionConstant3Vector, -360, -80)
    base.set_editor_property("constant", unreal.LinearColor(*colour, 1.0))
    metal = mel.create_material_expression(asset, unreal.MaterialExpressionConstant, -360, 50)
    metal.set_editor_property("r", metallic)
    rough = mel.create_material_expression(asset, unreal.MaterialExpressionConstant, -360, 160)
    rough.set_editor_property("r", roughness)
    mel.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(asset)
    library.save_loaded_asset(asset, only_if_is_dirty=False)
    return asset


coil = simple_material("M_PR005_CoilSteel_Rolled_v044", (0.205, 0.225, 0.238), 0.82, 0.46)
machined = simple_material("M_PR005_MachinedSteel_Worked_v044", (0.245, 0.270, 0.285), 0.84, 0.39)
stainless = simple_material("M_PR005_Stainless_Brushed_v044", (0.285, 0.305, 0.315), 0.76, 0.47)
galvanised = simple_material("M_PR005_Galvanised_Guard_v044", (0.235, 0.255, 0.265), 0.68, 0.57)
yellow_coated = simple_material("M_PR005_SafetyYellow_Coated_v044", (0.66, 0.31, 0.018), 0.16, 0.52)

replacements = {
    "M_PR005_SafetyYellow": yellow_coated,
    "MI_PR005_SafetyYellow_Layered_v044": yellow_coated,
    "M_PR005_DarkMachine": dark,
    "M_PR005_CoilSteel": coil,
    "M_PR005_MachinedSteel": machined,
    "M_PR005_Stainless": stainless,
    "M_PR005_Galvanised": galvanised,
}
override_counts = {key: 0 for key in replacements}
retained_counts = {material.get_name(): 0 for material in replacements.values()}
slot_override_counts = {"guard_safety_yellow": 0, "guard_galvanised_mesh": 0}
actor_count = 0
for actor in actors_api.get_all_level_actors():
    if unreal.Name("LB.Station.PR-005") not in actor.tags or not isinstance(actor, unreal.StaticMeshActor):
        continue
    component = actor.static_mesh_component
    slots = component.static_mesh.get_editor_property("static_materials") if component.static_mesh else []
    changed = False
    for index in range(component.get_num_materials()):
        current = component.get_material(index)
        if current is None:
            continue
        slot_name = str(slots[index].get_editor_property("imported_material_slot_name")) if index < len(slots) else ""
        slot_replacement = None
        slot_counter = None
        if "Guard_safety_yellow" in slot_name:
            slot_replacement, slot_counter = yellow_coated, "guard_safety_yellow"
        elif "Guard_galvanised_mesh" in slot_name:
            slot_replacement, slot_counter = galvanised, "guard_galvanised_mesh"
        if slot_replacement is not None:
            if current.get_path_name() != slot_replacement.get_path_name():
                component.set_material(index, slot_replacement)
                slot_override_counts[slot_counter] += 1
            retained_counts[slot_replacement.get_name()] += 1
            changed = True
            continue
        key = current.get_name()
        if key in retained_counts:
            retained_counts[key] += 1
            changed = True
            continue
        replacement = replacements.get(key)
        if replacement is not None:
            component.set_material(index, replacement)
            override_counts[key] += 1
            changed = True
    if changed:
        actor.tags = list(actor.tags) + [
            unreal.Name("LB.Asset.Candidate.v044"), unreal.Name("LB.Asset.CandidateNotPromoted")]
        actor_count += 1

if (override_counts["M_PR005_CoilSteel"] + retained_counts[coil.get_name()] < 1
        or override_counts["M_PR005_SafetyYellow"] + retained_counts[yellow_coated.get_name()] < 1):
    raise RuntimeError(f"Expected coil and yellow materials, got overrides={override_counts} retained={retained_counts}")
if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")
library.save_directory(ROOT, only_if_is_dirty=False, recursive=True)
library.save_directory(SHARED_ROOT, only_if_is_dirty=False, recursive=True)

payload = {
    "$schema": "line-boss/audit/press-shop-pr005-material-candidate-v044/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "LAYERED_PR005_MATERIALS_APPLIED__FULL_REGATES_AND_FRESH_VISUAL_REVIEW_REQUIRED__NOT_PROMOTED",
    "map": MAP,
    "base_map": "/Game/LineBoss/Maps/LB_PressShop_PR005LiveHMICandidate_v043",
    "surface_forge_scope": "Metal Paint Chips PBR textures through duplicated audited wrapper; painted machine surfaces only",
    "shared_material_master": SHARED_MASTER,
    "changed_actor_count": actor_count,
    "override_counts": override_counts,
    "retained_override_counts": retained_counts,
    "slot_override_counts": slot_override_counts,
    "safety_yellow_surface_forge_decision": "Rejected after fresh v044 render became near-black; retained Surface Forge only for dark painted machine surfaces.",
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR005_MATERIAL_V044_BUILD_PASS actors={actor_count} overrides={sum(override_counts.values())}")
unreal.SystemLibrary.quit_editor()
