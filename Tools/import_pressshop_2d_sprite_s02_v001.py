"""Import the first Press Shop visible-art sprite as an isolated UE asset.

The PNG is generated source art.  This pass creates a native Texture2D and an
unlit masked material only; it never opens or changes a level.  A later pass
will mount the material on one camera-facing plane in a cloned candidate map.
"""
import hashlib
import json
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SOURCE = PROJECT / "SourceAssets" / "Candidate" / "PressShop" / "PressShop2D_Sprites_v001" / "T_LB_PS_S02_DrawForm_Sprite_v001.png"
ROOT = "/Game/LineBoss/Candidates/PressShop/PressShop2DSprites_v001"
TEXTURES = ROOT + "/Textures"
MATERIALS = ROOT + "/Materials"
TEXTURE_NAME = "T_LB_PS_S02_DrawForm_Sprite_v001"
MATERIAL_NAME = "M_LB_PS_S02_DrawForm_Sprite_Unlit_v001"
RECEIPT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2d_sprite_s02_import_v001.json"

TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
MEL = unreal.MaterialEditingLibrary


def fail(message):
    raise RuntimeError("PRESSSHOP_2D_S02_SPRITE_IMPORT_FAIL: " + message)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def asset_path(folder, name):
    return folder + "/" + name


if not SOURCE.is_file():
    fail("missing generated source sprite '{}'".format(SOURCE))

texture_path = asset_path(TEXTURES, TEXTURE_NAME)
texture = unreal.load_asset(texture_path) if unreal.EditorAssetLibrary.does_asset_exist(texture_path) else None
if texture is None:
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(SOURCE),
        "destination_path": TEXTURES,
        "destination_name": TEXTURE_NAME,
        "automated": True,
        "replace_existing": False,
        "save": True,
    })
    TOOLS.import_asset_tasks([task])
    imported = list(task.get_editor_property("imported_object_paths") or [])
    if len(imported) != 1:
        fail("expected exactly one texture import, got {}".format(imported))
    texture = unreal.load_asset(imported[0])
if not isinstance(texture, unreal.Texture2D):
    fail("PNG did not resolve to a Texture2D")
texture.set_editor_property("srgb", True)
texture.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_DEFAULT)
texture.set_editor_property("never_stream", True)
unreal.EditorAssetLibrary.save_loaded_asset(texture, only_if_is_dirty=False)

material_path = asset_path(MATERIALS, MATERIAL_NAME)
material = unreal.load_asset(material_path) if unreal.EditorAssetLibrary.does_asset_exist(material_path) else None
if material is None:
    material = TOOLS.create_asset(MATERIAL_NAME, MATERIALS, unreal.Material, unreal.MaterialFactoryNew())
if not isinstance(material, unreal.Material):
    fail("could not create native sprite material")
if hasattr(MEL, "delete_all_material_expressions"):
    MEL.delete_all_material_expressions(material)
material.set_editor_properties({
    "blend_mode": unreal.BlendMode.BLEND_MASKED,
    "shading_model": unreal.MaterialShadingModel.MSM_UNLIT,
    "two_sided": True,
    "opacity_mask_clip_value": 0.08,
})
sample = MEL.create_material_expression(material, unreal.MaterialExpressionTextureSample, -440, 0)
sample.set_editor_properties({
    "texture": texture,
    "sampler_type": unreal.MaterialSamplerType.SAMPLERTYPE_COLOR,
})
MEL.connect_material_property(sample, "RGB", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
MEL.connect_material_property(sample, "A", unreal.MaterialProperty.MP_OPACITY_MASK)
MEL.recompile_material(material)
unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
unreal.EditorAssetLibrary.save_directory(ROOT, only_if_is_dirty=False, recursive=True)

receipt = {
    "status": "PASS__S02_VISIBLE_ART_SPRITE_IMPORTED_WITH_NATIVE_UNLIT_MASKED_MATERIAL__NO_MAP_TOUCHED",
    "map_loaded": False,
    "map_saved": False,
    "source_png": str(SOURCE),
    "source_sha256": sha256(SOURCE),
    "texture": texture.get_path_name(),
    "material": material.get_path_name(),
    "material_contract": "unlit masked surface; RGB to emissive and PNG alpha to opacity mask; two-sided; no lighting dependency",
    "next_gate": "clone the full 2.5D v001 candidate, mount one camera-facing S02 plane, and capture it with the fixed overview camera",
}
RECEIPT.parent.mkdir(parents=True, exist_ok=True)
RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_2D_S02_SPRITE_IMPORT_PASS=" + json.dumps(receipt, sort_keys=True))
