"""Build reusable PBR floor/wall materials for the Press Shop front end.

The curated Factory Environment textures are used only as licensed surface
inputs.  Line Boss owns the master/instances, tint language and application.
All outputs remain release candidates until fixed-camera visual review.
"""

from __future__ import annotations

import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
DEST = "/Game/LineBoss/Materials/FrontEnd"
MASTER_NAME = "M_LB_FrontEndPaintedConcrete_Master"
AUDIT = ROOT / "Saved/Audits/front_end_release_materials_v001.json"

TEXTURES = {
    "base": "/Game/LineBoss/Vendor/FactoryEnvironment/Textures/T_ConcretePillar01_BC.T_ConcretePillar01_BC",
    "normal": "/Game/LineBoss/Vendor/FactoryEnvironment/Textures/T_ConcretePillar01_N.T_ConcretePillar01_N",
    "orm": "/Game/LineBoss/Vendor/FactoryEnvironment/Textures/T_ConcretePillar01_ORM.T_ConcretePillar01_ORM",
}

# These are multiplicative linear-space paint tints, not sRGB swatches.  Values
# near 0.05 made the first candidate pads almost black after multiplication by
# the licensed concrete base texture.  The brighter linear values below retain
# concrete variation while restoring the blue/orange/red/green shop language
# visible in the approved references.
INSTANCES = {
    "MI_LB_Floor_Neutral": ((0.72, 0.76, 0.82, 1.0), 0.24, 0.08),
    "MI_LB_Floor_PR001_Blue": ((0.08, 0.42, 1.00, 1.0), 0.72, 0.10),
    "MI_LB_Floor_PR002_Orange": ((1.00, 0.31, 0.045, 1.0), 0.70, 0.10),
    "MI_LB_Floor_Hold_Red": ((0.95, 0.055, 0.035, 1.0), 0.76, 0.10),
    "MI_LB_Floor_PR003_BlueGreen": ((0.07, 0.55, 0.68, 1.0), 0.70, 0.10),
    "MI_LB_Floor_PR004_Grey": ((0.50, 0.58, 0.64, 1.0), 0.48, 0.10),
    "MI_LB_Floor_Walkway_Green": ((0.07, 0.66, 0.30, 1.0), 0.70, 0.12),
    "MI_LB_Wall_Concrete": ((0.78, 0.80, 0.84, 1.0), 0.20, 0.055),
    "MI_LB_Wall_DarkService": ((0.26, 0.31, 0.38, 1.0), 0.55, 0.065),
}


def load_texture(path: str) -> unreal.Texture:
    texture = unreal.load_asset(path)
    if not isinstance(texture, unreal.Texture):
        raise RuntimeError(f"Missing licensed texture input: {path}")
    return texture


def expression(material, klass, x, y):
    return unreal.MaterialEditingLibrary.create_material_expression(material, klass, x, y)


def build_master():
    library = unreal.EditorAssetLibrary
    path = f"{DEST}/{MASTER_NAME}"
    material = library.load_asset(path)
    if material is None:
        material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            MASTER_NAME, DEST, unreal.Material, unreal.MaterialFactoryNew()
        )
    if hasattr(unreal.MaterialEditingLibrary, "delete_all_material_expressions"):
        unreal.MaterialEditingLibrary.delete_all_material_expressions(material)

    material.set_editor_properties({"two_sided": False})

    uv = expression(material, unreal.MaterialExpressionTextureCoordinate, -1050, 0)
    uv.set_editor_properties({"u_tiling": 10.0, "v_tiling": 10.0})

    base_sample = expression(material, unreal.MaterialExpressionTextureSample, -820, -120)
    base_sample.set_editor_property("texture", load_texture(TEXTURES["base"]))
    unreal.MaterialEditingLibrary.connect_material_expressions(uv, "", base_sample, "UVs")

    tint = expression(material, unreal.MaterialExpressionVectorParameter, -820, 120)
    tint.set_editor_properties({
        "parameter_name": "ZoneTint",
        "default_value": unreal.LinearColor(0.42, 0.45, 0.48, 1.0),
    })
    tinted = expression(material, unreal.MaterialExpressionMultiply, -560, 0)
    unreal.MaterialEditingLibrary.connect_material_expressions(base_sample, "RGB", tinted, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(tint, "", tinted, "B")

    strength = expression(material, unreal.MaterialExpressionScalarParameter, -560, 160)
    strength.set_editor_properties({"parameter_name": "TintStrength", "default_value": 0.4})
    blend = expression(material, unreal.MaterialExpressionLinearInterpolate, -300, -20)
    unreal.MaterialEditingLibrary.connect_material_expressions(base_sample, "RGB", blend, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(tinted, "", blend, "B")
    unreal.MaterialEditingLibrary.connect_material_expressions(strength, "", blend, "Alpha")
    unreal.MaterialEditingLibrary.connect_material_property(blend, "", unreal.MaterialProperty.MP_BASE_COLOR)

    normal_sample = expression(material, unreal.MaterialExpressionTextureSample, -820, 330)
    normal_sample.set_editor_properties({
        "texture": load_texture(TEXTURES["normal"]),
        "sampler_type": unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL,
    })
    unreal.MaterialEditingLibrary.connect_material_expressions(uv, "", normal_sample, "UVs")
    unreal.MaterialEditingLibrary.connect_material_property(normal_sample, "RGB", unreal.MaterialProperty.MP_NORMAL)

    orm_sample = expression(material, unreal.MaterialExpressionTextureSample, -820, 560)
    orm_sample.set_editor_properties({
        "texture": load_texture(TEXTURES["orm"]),
        "sampler_type": unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR,
    })
    unreal.MaterialEditingLibrary.connect_material_expressions(uv, "", orm_sample, "UVs")
    unreal.MaterialEditingLibrary.connect_material_property(orm_sample, "R", unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
    unreal.MaterialEditingLibrary.connect_material_property(orm_sample, "G", unreal.MaterialProperty.MP_ROUGHNESS)
    unreal.MaterialEditingLibrary.connect_material_property(orm_sample, "B", unreal.MaterialProperty.MP_METALLIC)

    detail = expression(material, unreal.MaterialExpressionScalarParameter, -560, 710)
    detail.set_editor_properties({"parameter_name": "DetailNormalStrength", "default_value": 0.10})
    # Kept as a named contract parameter for future normal blending.  The
    # texture normal remains physically valid at candidate stage.

    unreal.MaterialEditingLibrary.recompile_material(material)
    library.save_loaded_asset(material, only_if_is_dirty=False)
    return material


def build_instance(name: str, parent, tint, strength: float, detail_strength: float):
    library = unreal.EditorAssetLibrary
    path = f"{DEST}/{name}"
    instance = library.load_asset(path)
    if instance is None:
        instance = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            name, DEST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew()
        )
    instance.set_editor_property("parent", parent)
    unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
        instance, "ZoneTint", unreal.LinearColor(*tint)
    )
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(instance, "TintStrength", strength)
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
        instance, "DetailNormalStrength", detail_strength
    )
    library.save_loaded_asset(instance, only_if_is_dirty=False)
    return instance


master = build_master()
records = []
for instance_name, values in INSTANCES.items():
    instance = build_instance(instance_name, master, *values)
    records.append({
        "asset": instance.get_path_name(),
        "tint": list(values[0]),
        "tint_strength": values[1],
        "detail_normal_strength": values[2],
    })

AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps({
    "status": "RELEASE_MATERIAL_CANDIDATE_NOT_PROMOTED",
    "master": master.get_path_name(),
    "licensed_texture_inputs": TEXTURES,
    "instances": records,
}, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_FRONT_END_RELEASE_MATERIALS_PASS instances={len(records)} audit={AUDIT}")
