"""Import the individual high-detail Press Shop sprite candidates as native UE assets.

This is source-asset only: it imports transparent PNGs and builds one unlit masked
material per sprite.  It deliberately does not load, mutate, or save any map.
"""
import hashlib
import json
from pathlib import Path

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SOURCE_ROOT = PROJECT / "SourceAssets" / "Candidate" / "PressShop" / "PressShop2D_Sprites_v001"
ROOT = "/Game/LineBoss/Candidates/PressShop/PressShop2DSprites_v004"
TEXTURES = ROOT + "/Textures"
MATERIALS = ROOT + "/Materials"
RECEIPT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2d_station_sprites_import_v004.json"

# These authority maps are evidence and must remain byte-identical.
PROTECTED_MAPS = {
    PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap": "5029c9d827d9a1d72c12f27ee757c9bc1e47febd5006ce6d7ba319aad2e7fec8",
    PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap": "cc09cf46d33e8a562d97f5a3bc35a5b42c9582d8e4650cf315694ebf340e4aa0",
}

ASSETS = (
    ("T_LB_PS_S01_StraightenerFeeder_Topdown_v002", "M_LB_PS_S01_StraightenerFeeder_Topdown_Unlit_v004"),
    ("T_LB_PS_S03_TrimPress_Topdown_v002", "M_LB_PS_S03_TrimPress_Topdown_Unlit_v004"),
    ("T_LB_PS_S04_PiercePress_Topdown_v002", "M_LB_PS_S04_PiercePress_Topdown_Unlit_v004"),
    ("T_LB_PS_S05_FlangeHem_Topdown_v002", "M_LB_PS_S05_FlangeHem_Topdown_Unlit_v004"),
    ("T_LB_PS_S06_VisionUnload_Topdown_v002", "M_LB_PS_S06_VisionUnload_Topdown_Unlit_v004"),
    ("T_LB_PS_TransferConveyor_Topdown_v001", "M_LB_PS_TransferConveyor_Topdown_Unlit_v004"),
    ("T_LB_PS_TransferGantry_Topdown_v001", "M_LB_PS_TransferGantry_Topdown_Unlit_v004"),
)

TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
MEL = unreal.MaterialEditingLibrary


def fail(message):
    raise RuntimeError("PRESSSHOP_2D_STATION_SPRITES_IMPORT_FAIL: " + message)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().lower()


def verify_protected_maps():
    for path, expected in PROTECTED_MAPS.items():
        if not path.is_file():
            fail("protected map missing: {}".format(path))
        actual = sha256(path)
        if actual != expected:
            fail("protected map hash mismatch: {}".format(path))


def get_or_import_texture(texture_name):
    png = SOURCE_ROOT / (texture_name + ".png")
    if not png.is_file():
        fail("source PNG missing: {}".format(png))
    asset_path = TEXTURES + "/" + texture_name
    texture = unreal.load_asset(asset_path) if unreal.EditorAssetLibrary.does_asset_exist(asset_path) else None
    if texture is None:
        task = unreal.AssetImportTask()
        task.set_editor_properties({
            "filename": str(png),
            "destination_path": TEXTURES,
            "destination_name": texture_name,
            "automated": True,
            "replace_existing": False,
            "save": True,
        })
        TOOLS.import_asset_tasks([task])
        paths = list(task.get_editor_property("imported_object_paths") or [])
        if len(paths) != 1:
            fail("expected one imported object for {}, got {}".format(texture_name, paths))
        texture = unreal.load_asset(paths[0])
    if not isinstance(texture, unreal.Texture2D):
        fail("{} did not import as Texture2D".format(texture_name))
    texture.set_editor_properties({
        "srgb": True,
        "compression_settings": unreal.TextureCompressionSettings.TC_DEFAULT,
        "never_stream": True,
    })
    unreal.EditorAssetLibrary.save_loaded_asset(texture, only_if_is_dirty=False)
    return texture, png


def get_or_build_material(material_name, texture):
    asset_path = MATERIALS + "/" + material_name
    material = unreal.load_asset(asset_path) if unreal.EditorAssetLibrary.does_asset_exist(asset_path) else None
    if material is None:
        material = TOOLS.create_asset(material_name, MATERIALS, unreal.Material, unreal.MaterialFactoryNew())
    if not isinstance(material, unreal.Material):
        fail("could not create material {}".format(material_name))
    MEL.delete_all_material_expressions(material)
    material.set_editor_properties({
        "blend_mode": unreal.BlendMode.BLEND_MASKED,
        "shading_model": unreal.MaterialShadingModel.MSM_UNLIT,
        "two_sided": True,
        "opacity_mask_clip_value": 0.08,
    })
    sample = MEL.create_material_expression(material, unreal.MaterialExpressionTextureSample, -420, 0)
    sample.set_editor_properties({
        "texture": texture,
        "sampler_type": unreal.MaterialSamplerType.SAMPLERTYPE_COLOR,
    })
    if not MEL.connect_material_property(sample, "RGB", unreal.MaterialProperty.MP_EMISSIVE_COLOR):
        fail("could not connect {} RGB to emissive".format(material_name))
    if not MEL.connect_material_property(sample, "A", unreal.MaterialProperty.MP_OPACITY_MASK):
        fail("could not connect {} alpha to opacity mask".format(material_name))
    MEL.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    return material


verify_protected_maps()
records = []
for texture_name, material_name in ASSETS:
    texture, source = get_or_import_texture(texture_name)
    material = get_or_build_material(material_name, texture)
    records.append({
        "source_png": str(source),
        "source_sha256": sha256(source),
        "texture": texture.get_path_name(),
        "material": material.get_path_name(),
        "alpha_contract": "source PNG alpha drives native masked opacity",
    })

unreal.EditorAssetLibrary.save_directory(ROOT, only_if_is_dirty=False, recursive=True)
verify_protected_maps()
receipt = {
    "status": "PASS__INDIVIDUAL_STATION_SPRITES_IMPORTED__NO_MAP_TOUCHED",
    "asset_count": len(records),
    "assets": records,
    "material_contract": "two-sided unlit masked materials; alpha is connected to opacity mask",
    "protected_maps_verified_before_and_after": True,
    "next_gate": "mount only in a fresh candidate map and inspect from the locked game camera",
}
RECEIPT.parent.mkdir(parents=True, exist_ok=True)
RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_2D_STATION_SPRITES_IMPORT_PASS=" + json.dumps(receipt, sort_keys=True))
