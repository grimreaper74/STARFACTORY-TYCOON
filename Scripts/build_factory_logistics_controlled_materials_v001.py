"""Build Line Boss-owned controlled PBR wrappers for licensed logistics UVs."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


DEST = "/Game/LineBoss/Shared/Logistics/Candidate_v001/Materials"
TEX = "/Game/LineBoss/Vendor/FactoryEnvironment/Logistics/Textures"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/factory_logistics_controlled_materials_v001.json"
SPECS = {
    "M_LB_Logistics_ForkliftBody_v001": {
        "base": f"{TEX}/T_ForkLift_BC", "normal": f"{TEX}/T_ForkLift_N", "orm": f"{TEX}/T_ForkLift_ORM",
        "tint": (1.0, 0.48, 0.035, 1.0), "strength": 0.62,
    },
    "M_LB_Logistics_ForkliftDetail_v001": {
        "base": f"{TEX}/T_ForkLiftDetails_BC", "normal": f"{TEX}/T_ForkLiftDetails_N", "orm": f"{TEX}/T_ForkLiftDetails_ORM",
        "tint": (0.09, 0.105, 0.12, 1.0), "strength": 0.22,
    },
    "M_LB_Logistics_Stillage_v001": {
        "base": f"{TEX}/T_PalletCart_BC", "normal": f"{TEX}/T_PalletCart_N", "orm": f"{TEX}/T_PalletCart_ORM",
        "tint": (0.18, 0.22, 0.25, 1.0), "strength": 0.32,
    },
    "M_LB_Logistics_PalletBlue_v001": {
        "base": f"{TEX}/T_PlasticPallet01_BC", "normal": f"{TEX}/T_PlasticPallet01_N", "orm": f"{TEX}/T_PlasticPallet01_ORM",
        "tint": (0.035, 0.22, 0.58, 1.0), "strength": 0.46,
    },
    "M_LB_Logistics_CrateYellow_v001": {
        "base": f"{TEX}/T_AssemblyLine01_BC", "normal": f"{TEX}/T_AssemblyLine01_N", "orm": f"{TEX}/T_AssemblyLine01_ORM",
        "tint": (1.0, 0.48, 0.035, 1.0), "strength": 0.38,
    },
}

library = unreal.EditorAssetLibrary
editing = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()


def texture(path):
    value = unreal.load_asset(path)
    if not isinstance(value, unreal.Texture):
        raise RuntimeError(f"Missing licensed logistics texture {path}")
    return value


def expression(material, klass, x, y):
    return editing.create_material_expression(material, klass, x, y)


def build(name, spec):
    path = f"{DEST}/{name}"
    material = library.load_asset(path) if library.does_asset_exist(path) else None
    if material is None:
        material = tools.create_asset(name, DEST, unreal.Material, unreal.MaterialFactoryNew())
    if hasattr(editing, "delete_all_material_expressions"):
        editing.delete_all_material_expressions(material)

    base = expression(material, unreal.MaterialExpressionTextureSample, -800, -120)
    base.texture = texture(spec["base"])
    tint = expression(material, unreal.MaterialExpressionConstant4Vector, -800, 80)
    tint.set_editor_property("constant", unreal.LinearColor(*spec["tint"]))
    multiplied = expression(material, unreal.MaterialExpressionMultiply, -540, -50)
    editing.connect_material_expressions(base, "RGB", multiplied, "A")
    editing.connect_material_expressions(tint, "", multiplied, "B")
    strength = expression(material, unreal.MaterialExpressionConstant, -540, 130)
    strength.set_editor_property("r", spec["strength"])
    blend = expression(material, unreal.MaterialExpressionLinearInterpolate, -280, -40)
    editing.connect_material_expressions(base, "RGB", blend, "A")
    editing.connect_material_expressions(multiplied, "", blend, "B")
    editing.connect_material_expressions(strength, "", blend, "Alpha")
    # The licensed maps are deliberately neutral.  Use the multiplied branch
    # directly so unattended UE builds cannot silently collapse a constant
    # Lerp alpha back to the un-tinted source during material recompilation.
    editing.connect_material_property(multiplied, "", unreal.MaterialProperty.MP_BASE_COLOR)

    normal = expression(material, unreal.MaterialExpressionTextureSample, -520, 360)
    normal.set_editor_properties({"texture": texture(spec["normal"]),
                                  "sampler_type": unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL})
    editing.connect_material_property(normal, "RGB", unreal.MaterialProperty.MP_NORMAL)
    orm = expression(material, unreal.MaterialExpressionTextureSample, -520, 590)
    orm.set_editor_properties({"texture": texture(spec["orm"]),
                               "sampler_type": unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR})
    editing.connect_material_property(orm, "R", unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
    editing.connect_material_property(orm, "G", unreal.MaterialProperty.MP_ROUGHNESS)
    editing.connect_material_property(orm, "B", unreal.MaterialProperty.MP_METALLIC)
    editing.recompile_material(material)
    library.save_loaded_asset(material, only_if_is_dirty=False)
    return material


rows = []
for name, spec in SPECS.items():
    material = build(name, spec)
    rows.append({"asset": material.get_path_name(), **spec})
library.save_directory(DEST, only_if_is_dirty=False, recursive=True)
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "$schema": "line-boss/audit/factory-logistics-controlled-materials-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "LICENSED_TEXTURE_WRAPPERS_BUILT__ISOLATED_VISUAL_GATE_REQUIRED__NOT_PROMOTED",
    "materials": rows, "promotion_authorized": False,
}, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_FACTORY_LOGISTICS_CONTROLLED_MATERIALS_PASS count={len(rows)}")
