"""Create v035 with facade-only dark industrial material calibration."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = "/Game/LineBoss/Maps/LB_PressTrainAFacadeLightingCandidate_v034"
TARGET = "/Game/LineBoss/Maps/LB_PressTrainAFacadeMaterialCandidate_v035"
MAT_ROOT = "/Game/LineBoss/Candidates/PressTrains/Shared/EnclosedFacadeMaterials_v035"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_facade_material_v035.json"
library = unreal.EditorAssetLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if library.does_asset_exist(TARGET):
    raise RuntimeError(f"Refusing to overwrite preserved candidate: {TARGET}")


def layered_surface(name, colour_a, colour_b, metallic, rough_a, rough_b, scale):
    path = f"{MAT_ROOT}/{name}"
    material = library.load_asset(path) if library.does_asset_exist(path) else asset_tools.create_asset(
        name, MAT_ROOT, unreal.Material, unreal.MaterialFactoryNew())
    if material is None:
        raise RuntimeError(path)
    mel.delete_all_material_expressions(material)
    noise = mel.create_material_expression(material, unreal.MaterialExpressionNoise, -520, 60)
    noise.set_editor_properties({
        "scale": scale, "quality": 2, "levels": 2,
        "output_min": 0.32, "output_max": 0.68, "turbulence": True,
    })
    base_a = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -520, -220)
    base_a.set_editor_property("constant", unreal.LinearColor(*colour_a, 1.0))
    base_b = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -520, -120)
    base_b.set_editor_property("constant", unreal.LinearColor(*colour_b, 1.0))
    base_lerp = mel.create_material_expression(material, unreal.MaterialExpressionLinearInterpolate, -220, -160)
    mel.connect_material_expressions(base_a, "", base_lerp, "A")
    mel.connect_material_expressions(base_b, "", base_lerp, "B")
    mel.connect_material_expressions(noise, "", base_lerp, "Alpha")
    metal = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -220, 20)
    metal.set_editor_property("r", metallic)
    rough_a_node = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -520, 280)
    rough_a_node.set_editor_property("r", rough_a)
    rough_b_node = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -520, 370)
    rough_b_node.set_editor_property("r", rough_b)
    rough_lerp = mel.create_material_expression(material, unreal.MaterialExpressionLinearInterpolate, -220, 320)
    mel.connect_material_expressions(rough_a_node, "", rough_lerp, "A")
    mel.connect_material_expressions(rough_b_node, "", rough_lerp, "B")
    mel.connect_material_expressions(noise, "", rough_lerp, "Alpha")
    mel.connect_material_property(base_lerp, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    mel.connect_material_property(rough_lerp, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(material)
    library.save_loaded_asset(material, only_if_is_dirty=False)
    return material


materials = {
    "grey": layered_surface(
        "M_CA_MW_PT_EnclosureGreyLayered_v035",
        (0.018, 0.024, 0.027), (0.042, 0.050, 0.053), 0.44, 0.54, 0.66, 0.080),
    "green": layered_surface(
        "M_CA_MW_PT_EnclosureGreenLayered_v035",
        (0.006, 0.030, 0.021), (0.014, 0.064, 0.044), 0.30, 0.52, 0.63, 0.078),
}

if not levels.new_level_from_template(TARGET, SOURCE):
    raise RuntimeError(f"Could not create v035 from v034: {TARGET}")

facade_actors = []
reassigned = []
for actor in actors_api.get_all_level_actors():
    tags = {str(tag) for tag in actor.tags}
    if "LB.PressTrain.Fixed.EnclosedFacade" not in tags:
        continue
    facade_actors.append(actor.get_actor_label())
    component = actor.static_mesh_component
    for index, slot_name in enumerate(component.get_material_slot_names()):
        slot = str(slot_name)
        if "ServiceGrey" in slot:
            component.set_material(index, materials["grey"])
            reassigned.append({"actor": actor.get_actor_label(), "slot": slot, "material": "grey"})
        elif "CairnwellGreen" in slot:
            component.set_material(index, materials["green"])
            reassigned.append({"actor": actor.get_actor_label(), "slot": slot, "material": "green"})

for actor in actors_api.get_all_level_actors():
    if "LB.Validation.FacadeLighting" in {str(tag) for tag in actor.tags}:
        actor.get_editor_property("rect_light_component").set_editor_property("intensity", 205.0)

scope_count = 0
for actor in actors_api.get_all_level_actors():
    tags = [str(tag) for tag in actor.tags]
    if "LB.PressTrain.TrainA.Isolated" in tags:
        scope_count += 1
        if "LB.Asset.Candidate.v035" not in tags:
            tags.append("LB.Asset.Candidate.v035")
            actor.set_editor_property("tags", [unreal.Name(tag) for tag in tags])

failures = []
if len(facade_actors) != 7 or len(reassigned) != 14 or scope_count != 169:
    failures.append(
        f"cardinality mismatch facades={len(facade_actors)} reassigned={len(reassigned)} scope={scope_count}")
if not levels.save_current_level():
    failures.append("could not save v035 facade-material candidate")
library.save_directory(MAT_ROOT, only_if_is_dirty=False, recursive=True)
report = {
    "$schema": "cairnwell/audit/press-train-a-facade-material-v035/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": (
        "PASS__PRESS_TRAIN_A_V035_FACADE_ONLY_DARK_FOUNDRY_GREY_AND_DEEP_CAIRNWELL_GREEN_LAYERING__EXACT_STATIC_AND_FRESH_PRO_VISUAL_GATES_REQUIRED__NOT_PROMOTED"
        if not failures else "FAIL__PRESS_TRAIN_A_V035_FACADE_MATERIAL__NOT_PROMOTED"),
    "source_map": SOURCE, "map": TARGET, "material_root": MAT_ROOT,
    "facade_actors": facade_actors, "reassigned_slots": reassigned,
    "facade_fill_intensity": 205.0, "scope_actor_count": scope_count,
    "world_placement": "TBC_NOT_INVENTED", "production_map_changed": False,
    "accepted_pr010_map_changed": False, "failures": failures,
    "promotion_authorized": False, "press_shop_complete": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
