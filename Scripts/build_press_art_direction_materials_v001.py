"""Create the isolated, exact-palette native material lane for Press art direction.

This intentionally creates new project-owned materials instead of altering the
receipted S02, StagePack, or MaterialFlow asset closures.  Runtime components
may opt into these palette materials as reversible overrides; their source
meshes and original material assignments remain intact.
"""

from __future__ import annotations

import json
import traceback
from datetime import datetime, timezone
from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir()).resolve()
EXPECTED_PROJECT = Path(r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8").resolve()
DEST = "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/ArtDirection_v001"
MATERIAL_DEST = DEST + "/Materials"
MASTER_NAME = "M_CA_MW_PT_ArtDirectionPalette_Master_v001"
MASTER_PATH = MATERIAL_DEST + "/" + MASTER_NAME + "." + MASTER_NAME
AUDIT_DIR = PROJECT / "Saved/Audits/OneFactory/Press/ArtDirection_v001"
RECEIPT = AUDIT_DIR / "native_palette_materials_receipt_v001.json"
FAILURE = AUDIT_DIR / "native_palette_materials_failure_v001.json"

# The six literal authority tokens use the exact sRGB hex values from
# Docs/BRAND_IDENTITY_AUTHORITY.md.  The pale floor zone is deliberately named
# a lightened Cairnwell derivative rather than misrepresented as a seventh
# brand token.
PALETTE = {
    "CairnwellGreen": {
        "name": "MI_CA_MW_PT_AD_CairnwellGreen_v001",
        "hex": "#1F4B44", "metallic": 0.12, "roughness": 0.46,
        "authority": "Cairnwell Green",
    },
    "FoundryCharcoal": {
        "name": "MI_CA_MW_PT_AD_FoundryCharcoal_v001",
        "hex": "#202428", "metallic": 0.18, "roughness": 0.50,
        "authority": "Foundry Charcoal",
    },
    "SteelGrey": {
        "name": "MI_CA_MW_PT_AD_SteelGrey_v001",
        "hex": "#70777C", "metallic": 0.30, "roughness": 0.38,
        "authority": "Steel Grey",
    },
    "WarmWhite": {
        "name": "MI_CA_MW_PT_AD_WarmWhite_v001",
        "hex": "#F3F1E9", "metallic": 0.0, "roughness": 0.58,
        "authority": "Warm White",
    },
    "SafetyYellow": {
        "name": "MI_CA_MW_PT_AD_SafetyYellow_v001",
        "hex": "#F2C300", "metallic": 0.08, "roughness": 0.42,
        "authority": "Safety Yellow",
    },
    "SignalRed": {
        "name": "MI_CA_MW_PT_AD_SignalRed_v001",
        "hex": "#C7352C", "metallic": 0.05, "roughness": 0.42,
        "authority": "Signal Red",
    },
    "PaleGreenZone": {
        "name": "MI_CA_MW_PT_AD_PaleGreenZone_v001",
        "hex": "#A7C6B0", "metallic": 0.0, "roughness": 0.68,
        "authority": "lightened Cairnwell derivative (floor-zone only)",
    },
}

SOURCE_MATERIALS = (
    "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/SharedTrainModules_v003/"
    "Materials/MI_CA_MW_PT_CairnwellGreen_v001.MI_CA_MW_PT_CairnwellGreen_v001",
    "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/SharedTrainModules_v003/"
    "Materials/MI_CA_MW_PT_FoundryCharcoal_v001.MI_CA_MW_PT_FoundryCharcoal_v001",
    "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/SharedTrainModules_v003/"
    "Materials/MI_CA_MW_PT_ServiceGrey_v001.MI_CA_MW_PT_ServiceGrey_v001",
    "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/SharedTrainModules_v003/"
    "Materials/MI_CA_MW_PT_SafetyYellow_v001.MI_CA_MW_PT_SafetyYellow_v001",
    "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002/"
    "Materials/MI_CA_MW_PT_StampedPanel_v001.MI_CA_MW_PT_StampedPanel_v001",
)

LIBRARY = unreal.EditorAssetLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
EDITING = unreal.MaterialEditingLibrary


def fail(message: str) -> None:
    raise RuntimeError("PRESS_ART_DIRECTION_MATERIALS_V001_FAIL: " + message)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def srgb_hex_to_linear(value: str) -> unreal.LinearColor:
    if len(value) != 7 or not value.startswith("#"):
        fail("invalid sRGB hex: " + value)
    channels = [int(value[index:index + 2], 16) / 255.0 for index in (1, 3, 5)]
    linear = [channel / 12.92 if channel <= 0.04045
              else ((channel + 0.055) / 1.055) ** 2.4 for channel in channels]
    return unreal.LinearColor(linear[0], linear[1], linear[2], 1.0)


def color_list(value: unreal.LinearColor) -> list[float]:
    return [round(float(value.r), 9), round(float(value.g), 9),
            round(float(value.b), 9), round(float(value.a), 9)]


def material_usage_instanced_static_meshes():
    wanted = "MATUSAGE_INSTANCED_STATIC_MESHES"
    if hasattr(unreal.MaterialUsage, wanted):
        return getattr(unreal.MaterialUsage, wanted)
    candidates = [name for name in dir(unreal.MaterialUsage)
                  if "INSTANCED" in name.upper()
                  and "STATIC" in name.upper()
                  and "MESH" in name.upper()
                  and "SKINNED" not in name.upper()]
    if len(candidates) != 1:
        fail("could not resolve instanced-static-mesh material usage: " + str(candidates))
    return getattr(unreal.MaterialUsage, candidates[0])


def expression(material, cls, x, y):
    node = EDITING.create_material_expression(material, cls, x, y)
    if node is None:
        fail("could not create material expression " + str(cls))
    return node


def connect_property(source, output, property_name, label: str) -> None:
    if not EDITING.connect_material_property(source, output, property_name):
        fail("material graph connection failed: " + label)


def preflight() -> None:
    if PROJECT != EXPECTED_PROJECT:
        fail("project identity drift: " + str(PROJECT))
    if str(unreal.SystemLibrary.get_game_name()) != "LineBossCarFactory":
        fail("game identity drift")
    existing = [MASTER_PATH] + [MATERIAL_DEST + "/" + spec["name"] + "." + spec["name"]
                                for spec in PALETTE.values()]
    existing = [path for path in existing if LIBRARY.does_asset_exist(path)]
    if existing:
        fail("refusing to overwrite palette assets: " + str(existing))
    if LIBRARY.does_directory_exist(DEST) and LIBRARY.list_assets(
            DEST, recursive=True, include_folder=False):
        fail("destination namespace is not empty")
    for path in SOURCE_MATERIALS:
        asset = unreal.load_asset(path)
        if asset is None or not isinstance(asset, unreal.MaterialInterface):
            fail("required unchanged source material does not resolve: " + path)


def create_master() -> unreal.Material:
    material = TOOLS.create_asset(
        MASTER_NAME, MATERIAL_DEST, unreal.Material, unreal.MaterialFactoryNew())
    if not isinstance(material, unreal.Material):
        fail("could not create palette master")
    material.set_editor_properties({
        "two_sided": False,
        "blend_mode": unreal.BlendMode.BLEND_OPAQUE,
    })
    usage = material_usage_instanced_static_meshes()
    EDITING.set_base_material_usage(material, usage, True)
    if not bool(material.get_editor_property("used_with_instanced_static_meshes")):
        fail("palette master rejected instanced-static-mesh usage")

    base = expression(material, unreal.MaterialExpressionVectorParameter, -600, -240)
    base.set_editor_properties({
        "parameter_name": "PaletteBaseColor",
        "default_value": srgb_hex_to_linear("#70777C"),
    })
    connect_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR, "PaletteBaseColor")
    metallic = expression(material, unreal.MaterialExpressionScalarParameter, -600, -80)
    metallic.set_editor_properties({"parameter_name": "Metallic", "default_value": 0.15})
    connect_property(metallic, "", unreal.MaterialProperty.MP_METALLIC, "Metallic")
    roughness = expression(material, unreal.MaterialExpressionScalarParameter, -600, 80)
    roughness.set_editor_properties({"parameter_name": "Roughness", "default_value": 0.45})
    connect_property(roughness, "", unreal.MaterialProperty.MP_ROUGHNESS, "Roughness")
    specular = expression(material, unreal.MaterialExpressionScalarParameter, -600, 240)
    specular.set_editor_properties({"parameter_name": "Specular", "default_value": 0.35})
    connect_property(specular, "", unreal.MaterialProperty.MP_SPECULAR, "Specular")

    EDITING.recompile_material(material)
    if not LIBRARY.save_loaded_asset(material, only_if_is_dirty=False):
        fail("could not save palette master")
    if not bool(material.get_editor_property("used_with_instanced_static_meshes")):
        fail("palette master lost instanced-static-mesh usage after save")
    return material


def create_instances(master: unreal.Material) -> dict[str, unreal.MaterialInstanceConstant]:
    result = {}
    for semantic, spec in PALETTE.items():
        instance = TOOLS.create_asset(
            spec["name"], MATERIAL_DEST, unreal.MaterialInstanceConstant,
            unreal.MaterialInstanceConstantFactoryNew())
        if not isinstance(instance, unreal.MaterialInstanceConstant):
            fail("could not create material instance: " + semantic)
        instance.set_editor_property("parent", master)
        expected_color = srgb_hex_to_linear(spec["hex"])
        EDITING.set_material_instance_vector_parameter_value(
            instance, "PaletteBaseColor", expected_color)
        EDITING.set_material_instance_scalar_parameter_value(
            instance, "Metallic", float(spec["metallic"]))
        EDITING.set_material_instance_scalar_parameter_value(
            instance, "Roughness", float(spec["roughness"]))
        EDITING.set_material_instance_scalar_parameter_value(instance, "Specular", 0.35)
        EDITING.update_material_instance(instance)
        actual_color = EDITING.get_material_instance_vector_parameter_value(
            instance, "PaletteBaseColor")
        if color_list(actual_color) != color_list(expected_color):
            fail("sRGB-linear palette value drift: " + semantic)
        if not LIBRARY.save_loaded_asset(instance, only_if_is_dirty=False):
            fail("could not save material instance: " + semantic)
        result[semantic] = instance
    return result


def main() -> None:
    evidence = {
        "$schema": "lineboss/onefactory/press/art-direction-v001/native-palette-materials/v1",
        "generated_utc": utc_now(),
        "destination": DEST,
        "source_assets_mutated": False,
        "map_opened_or_saved": False,
        "content_writes": [DEST],
        "brand_authority": "Docs/BRAND_IDENTITY_AUTHORITY.md",
        "train_a_accent_policy": "replace off-palette blue with Warm White at runtime",
    }
    try:
        preflight()
        master = create_master()
        instances = create_instances(master)
        expected_assets = {MASTER_PATH}
        expected_assets.update(instance.get_path_name() for instance in instances.values())
        registry = set(str(path) for path in LIBRARY.list_assets(
            DEST, recursive=True, include_folder=False))
        if registry != expected_assets:
            fail("native palette package closure drift")
        evidence.update({
            "status": "PASS__PRESS_ART_DIRECTION_V001_NATIVE_PALETTE_MATERIALS",
            "master": master.get_path_name(),
            "material_count": len(instances),
            "materials": {
                semantic: {
                    "path": instance.get_path_name(),
                    "hex_srgb": PALETTE[semantic]["hex"],
                    "linear_rgba": color_list(srgb_hex_to_linear(PALETTE[semantic]["hex"])),
                    "authority": PALETTE[semantic]["authority"],
                    "metallic": PALETTE[semantic]["metallic"],
                    "roughness": PALETTE[semantic]["roughness"],
                }
                for semantic, instance in instances.items()
            },
            "native_assets": sorted(registry),
        })
        AUDIT_DIR.mkdir(parents=True, exist_ok=True)
        RECEIPT.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
        unreal.log("PRESS_ART_DIRECTION_MATERIALS_V001_PASS=" + str(RECEIPT))
    except Exception as error:
        AUDIT_DIR.mkdir(parents=True, exist_ok=True)
        failure = {**evidence,
                   "status": "FAIL_CLOSED__PRESS_ART_DIRECTION_V001_NATIVE_PALETTE_MATERIALS",
                   "error": str(error), "traceback": traceback.format_exc()}
        FAILURE.write_text(json.dumps(failure, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
        unreal.log_error("PRESS_ART_DIRECTION_MATERIALS_V001_FAIL=" + str(error))
        raise
    finally:
        unreal.SystemLibrary.quit_editor()


if __name__ == "__main__":
    main()
