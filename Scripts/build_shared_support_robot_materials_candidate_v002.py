"""Build corrected shared Surface Forge-derived robot paint Candidate v002.

Only the three selectively preserved Metal Paint Chips textures are consumed.\nThis revision uses their required virtual samplers and valid OneMinus pins.
No CR01/MR01 mesh, Blueprint, map, accepted baseline or vendor source asset is
modified.  The material family remains a candidate until it is bound to the
robots and passes fresh Unreal fixed-camera review.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
DEST = "/Game/LineBoss/Robots/Shared/Materials/Candidate_v002"
MASTER_NAME = "M_LB_SupportRobot_LayeredPaint_v002"
MASTER_PATH = f"{DEST}/{MASTER_NAME}"
AUDIT = ROOT / "Saved/Audits/lb_support_robot_shared_materials_candidate_v002.json"

TEXTURES = {
    "base": "/Game/Surface_Forge/Textures/Metal_Paint_Chips/T_Base_Color_Metal_Paint_Chips.T_Base_Color_Metal_Paint_Chips",
    "normal": "/Game/Surface_Forge/Textures/Metal_Paint_Chips/T_Normal_Metal_Paint_Chips.T_Normal_Metal_Paint_Chips",
    "ord": "/Game/Surface_Forge/Textures/Metal_Paint_Chips/T_ORD_Metal_Paint_Chips.T_ORD_Metal_Paint_Chips",
}

INSTANCE_SPECS = {
    "MI_LB_Robot_BodyCharcoal_Restored_v002": {
        "hex": "#202428", "dust": 0.08, "coverage": 0.86, "roughness": 0.56, "wear": 3.4,
    },
    "MI_LB_Robot_BodyCharcoal_Mothballed_v002": {
        "hex": "#202428", "dust": 0.42, "coverage": 0.67, "roughness": 0.72, "wear": 3.0,
    },
    "MI_LB_Robot_SafetyYellow_Restored_v002": {
        "hex": "#F2C300", "dust": 0.10, "coverage": 0.88, "roughness": 0.54, "wear": 3.6,
    },
    "MI_LB_Robot_SafetyYellow_Mothballed_v002": {
        "hex": "#F2C300", "dust": 0.38, "coverage": 0.69, "roughness": 0.70, "wear": 3.1,
    },
    "MI_LB_Robot_CairnwellGreen_Restored_v002": {
        "hex": "#1F4B44", "dust": 0.08, "coverage": 0.87, "roughness": 0.55, "wear": 3.5,
    },
    "MI_LB_Robot_CairnwellGreen_Mothballed_v002": {
        "hex": "#1F4B44", "dust": 0.40, "coverage": 0.68, "roughness": 0.71, "wear": 3.0,
    },
    "MI_LB_Robot_ServiceGrey_Restored_v002": {
        "hex": "#63696A", "dust": 0.07, "coverage": 0.90, "roughness": 0.52, "wear": 3.7,
    },
    "MI_LB_Robot_ServiceGrey_Mothballed_v002": {
        "hex": "#63696A", "dust": 0.36, "coverage": 0.72, "roughness": 0.69, "wear": 3.1,
    },
}

lib = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary


def require(path: str, cls):
    asset = lib.load_asset(path)
    if asset is None or not isinstance(asset, cls):
        raise RuntimeError(f"Missing required {cls.__name__}: {path}")
    return asset


def expr(material, cls, x, y):
    return mel.create_material_expression(material, cls, x, y)


def srgb_hex_to_linear(value: str) -> unreal.LinearColor:
    channels = [int(value[index:index + 2], 16) / 255.0 for index in (1, 3, 5)]
    linear = [channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4 for channel in channels]
    return unreal.LinearColor(linear[0], linear[1], linear[2], 1.0)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


existing = [path for path in [MASTER_PATH, *[f"{DEST}/{name}" for name in INSTANCE_SPECS]] if lib.does_asset_exist(path)]
if existing:
    raise RuntimeError(f"Refusing to overwrite preserved shared-material candidate assets: {existing}")

base_texture = require(TEXTURES["base"], unreal.Texture2D)
normal_texture = require(TEXTURES["normal"], unreal.Texture2D)
ord_texture = require(TEXTURES["ord"], unreal.Texture2D)

material = tools.create_asset(MASTER_NAME, DEST, unreal.Material, unreal.MaterialFactoryNew())
if material is None:
    raise RuntimeError(f"Could not create {MASTER_PATH}")
material.set_editor_properties({"two_sided": False, "blend_mode": unreal.BlendMode.BLEND_OPAQUE})

# Shared UVs for the lightweight three-texture Surface Forge subset.
uv = expr(material, unreal.MaterialExpressionTextureCoordinate, -1500, 0)
texture_scale = expr(material, unreal.MaterialExpressionScalarParameter, -1500, 110)
texture_scale.set_editor_properties({"parameter_name": "TextureScale", "default_value": 2.6})
scaled_uv = expr(material, unreal.MaterialExpressionMultiply, -1280, 20)
mel.connect_material_expressions(uv, "", scaled_uv, "A")
mel.connect_material_expressions(texture_scale, "", scaled_uv, "B")

base = expr(material, unreal.MaterialExpressionTextureSample, -1060, -330)
base.set_editor_properties({"texture": base_texture, "sampler_type": unreal.MaterialSamplerType.SAMPLERTYPE_VIRTUAL_COLOR})
mel.connect_material_expressions(scaled_uv, "", base, "UVs")
normal = expr(material, unreal.MaterialExpressionTextureSample, -1060, 180)
normal.set_editor_properties({"texture": normal_texture, "sampler_type": unreal.MaterialSamplerType.SAMPLERTYPE_VIRTUAL_NORMAL})
mel.connect_material_expressions(scaled_uv, "", normal, "UVs")
ord_sample = expr(material, unreal.MaterialExpressionTextureSample, -1060, 590)
ord_sample.set_editor_properties({"texture": ord_texture, "sampler_type": unreal.MaterialSamplerType.SAMPLERTYPE_VIRTUAL_LINEAR_COLOR})
mel.connect_material_expressions(scaled_uv, "", ord_sample, "UVs")

# Derive a restrained paint/chip mask from the authored texture instead of
# multiplying vendor colour directly into Cairnwell colours.
channel_delta = expr(material, unreal.MaterialExpressionSubtract, -820, -360)
mel.connect_material_expressions(base, "R", channel_delta, "A")
mel.connect_material_expressions(base, "B", channel_delta, "B")
wear_contrast = expr(material, unreal.MaterialExpressionScalarParameter, -820, -250)
wear_contrast.set_editor_properties({"parameter_name": "WearContrast", "default_value": 3.4})
amplified = expr(material, unreal.MaterialExpressionMultiply, -610, -330)
mel.connect_material_expressions(channel_delta, "", amplified, "A")
mel.connect_material_expressions(wear_contrast, "", amplified, "B")
coverage = expr(material, unreal.MaterialExpressionScalarParameter, -610, -210)
coverage.set_editor_properties({"parameter_name": "PaintCoverageBias", "default_value": 0.82})
biased = expr(material, unreal.MaterialExpressionAdd, -390, -300)
mel.connect_material_expressions(amplified, "", biased, "A")
mel.connect_material_expressions(coverage, "", biased, "B")
paint_mask = expr(material, unreal.MaterialExpressionSaturate, -180, -300)
mel.connect_material_expressions(biased, "", paint_mask, "")

exposed_colour = expr(material, unreal.MaterialExpressionVectorParameter, -390, -520)
exposed_colour.set_editor_properties({
    "parameter_name": "ExposedMetalColour",
    "default_value": unreal.LinearColor(0.035, 0.045, 0.055, 1.0),
})
paint_colour = expr(material, unreal.MaterialExpressionVectorParameter, -390, -440)
paint_colour.set_editor_properties({
    "parameter_name": "PaintColour",
    "default_value": srgb_hex_to_linear("#202428"),
})
painted_colour = expr(material, unreal.MaterialExpressionLinearInterpolate, 40, -420)
mel.connect_material_expressions(exposed_colour, "", painted_colour, "A")
mel.connect_material_expressions(paint_colour, "", painted_colour, "B")
mel.connect_material_expressions(paint_mask, "", painted_colour, "Alpha")

# Dust uses the ORD occlusion pattern as a crevice mask. This is a reusable
# hook, not a claim that the final seven-year condition masks are complete.
inverse_ao = expr(material, unreal.MaterialExpressionOneMinus, -620, 520)
mel.connect_material_expressions(ord_sample, "R", inverse_ao, "")
dust_amount = expr(material, unreal.MaterialExpressionScalarParameter, -390, 450)
dust_amount.set_editor_properties({"parameter_name": "DustAmount", "default_value": 0.08})
dust_mask_raw = expr(material, unreal.MaterialExpressionMultiply, -390, 550)
mel.connect_material_expressions(inverse_ao, "", dust_mask_raw, "A")
mel.connect_material_expressions(dust_amount, "", dust_mask_raw, "B")
dust_mask = expr(material, unreal.MaterialExpressionSaturate, -180, 520)
mel.connect_material_expressions(dust_mask_raw, "", dust_mask, "")
dust_colour = expr(material, unreal.MaterialExpressionVectorParameter, 40, -300)
dust_colour.set_editor_properties({
    "parameter_name": "DustColour",
    "default_value": srgb_hex_to_linear("#6A6253"),
})
final_colour = expr(material, unreal.MaterialExpressionLinearInterpolate, 300, -390)
mel.connect_material_expressions(painted_colour, "", final_colour, "A")
mel.connect_material_expressions(dust_colour, "", final_colour, "B")
mel.connect_material_expressions(dust_mask, "", final_colour, "Alpha")
mel.connect_material_property(final_colour, "", unreal.MaterialProperty.MP_BASE_COLOR)

flat_normal = expr(material, unreal.MaterialExpressionConstant3Vector, -820, 250)
flat_normal.set_editor_property("constant", unreal.LinearColor(0.5, 0.5, 1.0, 1.0))
normal_strength = expr(material, unreal.MaterialExpressionScalarParameter, -820, 340)
normal_strength.set_editor_properties({"parameter_name": "NormalStrength", "default_value": 0.22})
normal_blend = expr(material, unreal.MaterialExpressionLinearInterpolate, -390, 260)
mel.connect_material_expressions(flat_normal, "", normal_blend, "A")
mel.connect_material_expressions(normal, "RGB", normal_blend, "B")
mel.connect_material_expressions(normal_strength, "", normal_blend, "Alpha")
mel.connect_material_property(normal_blend, "", unreal.MaterialProperty.MP_NORMAL)

base_roughness = expr(material, unreal.MaterialExpressionScalarParameter, -180, 700)
base_roughness.set_editor_properties({"parameter_name": "BaseRoughness", "default_value": 0.56})
roughness_variation = expr(material, unreal.MaterialExpressionScalarParameter, -180, 790)
roughness_variation.set_editor_properties({"parameter_name": "RoughnessVariation", "default_value": 0.28})
surface_roughness = expr(material, unreal.MaterialExpressionLinearInterpolate, 40, 690)
mel.connect_material_expressions(base_roughness, "", surface_roughness, "A")
mel.connect_material_expressions(ord_sample, "G", surface_roughness, "B")
mel.connect_material_expressions(roughness_variation, "", surface_roughness, "Alpha")
dust_roughness = expr(material, unreal.MaterialExpressionScalarParameter, 40, 800)
dust_roughness.set_editor_properties({"parameter_name": "DustRoughness", "default_value": 0.88})
final_roughness = expr(material, unreal.MaterialExpressionLinearInterpolate, 300, 700)
mel.connect_material_expressions(surface_roughness, "", final_roughness, "A")
mel.connect_material_expressions(dust_roughness, "", final_roughness, "B")
mel.connect_material_expressions(dust_mask, "", final_roughness, "Alpha")
mel.connect_material_property(final_roughness, "", unreal.MaterialProperty.MP_ROUGHNESS)

inverse_paint = expr(material, unreal.MaterialExpressionOneMinus, 40, 0)
mel.connect_material_expressions(paint_mask, "", inverse_paint, "")
exposed_metallic = expr(material, unreal.MaterialExpressionScalarParameter, 40, 90)
exposed_metallic.set_editor_properties({"parameter_name": "ExposedMetallic", "default_value": 0.72})
metallic_raw = expr(material, unreal.MaterialExpressionMultiply, 300, 20)
mel.connect_material_expressions(inverse_paint, "", metallic_raw, "A")
mel.connect_material_expressions(exposed_metallic, "", metallic_raw, "B")
inverse_dust = expr(material, unreal.MaterialExpressionOneMinus, 300, 120)
mel.connect_material_expressions(dust_mask, "", inverse_dust, "")
metallic = expr(material, unreal.MaterialExpressionMultiply, 520, 40)
mel.connect_material_expressions(metallic_raw, "", metallic, "A")
mel.connect_material_expressions(inverse_dust, "", metallic, "B")
mel.connect_material_property(metallic, "", unreal.MaterialProperty.MP_METALLIC)
mel.connect_material_property(ord_sample, "R", unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)

mel.recompile_material(material)
lib.save_loaded_asset(material, only_if_is_dirty=False)

instance_rows = []
for name, spec in INSTANCE_SPECS.items():
    instance = tools.create_asset(name, DEST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    if instance is None:
        raise RuntimeError(f"Could not create {DEST}/{name}")
    instance.set_editor_property("parent", material)
    mel.set_material_instance_vector_parameter_value(instance, "PaintColour", srgb_hex_to_linear(spec["hex"]))
    mel.set_material_instance_vector_parameter_value(instance, "ExposedMetalColour", srgb_hex_to_linear("#252A2D"))
    mel.set_material_instance_vector_parameter_value(instance, "DustColour", srgb_hex_to_linear("#6A6253"))
    scalar_values = {
        "TextureScale": 2.6,
        "WearContrast": spec["wear"],
        "PaintCoverageBias": spec["coverage"],
        "DustAmount": spec["dust"],
        "NormalStrength": 0.22,
        "BaseRoughness": spec["roughness"],
        "RoughnessVariation": 0.28,
        "DustRoughness": 0.88,
        "ExposedMetallic": 0.72,
    }
    for parameter, value in scalar_values.items():
        mel.set_material_instance_scalar_parameter_value(instance, parameter, float(value))
    mel.update_material_instance(instance)
    lib.save_loaded_asset(instance, only_if_is_dirty=False)
    instance_rows.append({
        "asset": f"{DEST}/{name}",
        "paint_hex_srgb": spec["hex"],
        "condition": "MOTHBALLED" if "Mothballed" in name else "RESTORED_WITH_RETAINED_AGE",
        "scalar_parameters": scalar_values,
    })

unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

texture_rows = []
for role, object_path in TEXTURES.items():
    relative = object_path.split("/Game/", 1)[1].split(".", 1)[0] + ".uasset"
    disk_path = ROOT / "Content" / Path(relative)
    texture_rows.append({
        "role": role,
        "asset": object_path,
        "disk_path": str(disk_path),
        "bytes": disk_path.stat().st_size,
        "sha256": sha256(disk_path),
    })

result = {
    "$schema": "line-boss/audit/lb-support-robot-shared-materials-candidate-v002",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "SHARED_MATERIAL_CANDIDATE_BUILT__ROBOT_BINDING_AND_VISUAL_GATES_OPEN__NOT_PROMOTED",
    "master": MASTER_PATH,
    "instances": instance_rows,
    "surface_forge_textures": texture_rows,
    "vendor_master_material_used": False,
    "vendor_dependency_expansion_avoided": True,
    "source_assets_modified": False,
    "maps_modified": False,
    "material_intent": [
        "authoritative Cairnwell colours are applied directly, not multiplied by vendor base colour",
        "selective paint-chip normal/ORD variation",
        "parameterised paint coverage, exposed metal, roughness and crevice dust",
        "separate mothballed and restored-with-retained-age instances"
    ],
    "open_gates": [
        "bind only to audited semantic material slots on CR01 and MR01 candidates",
        "mesh/UV-specific wear, water streak, grease, oxidation and service-witness masks",
        "shader compile/log gate in a fresh Unreal process",
        "fresh fixed-camera Unreal comparison against both Pro sheets",
        "performance and packaged-runtime validation"
    ],
    "promotion_authorized": False
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
unreal.log(f"LINE_BOSS_SHARED_SUPPORT_ROBOT_MATERIALS_V002_BUILT instances={len(instance_rows)} audit={AUDIT}")
unreal.SystemLibrary.quit_editor()


