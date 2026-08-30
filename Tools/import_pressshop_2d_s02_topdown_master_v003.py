"""Import the genuinely transparent top-down S02 master with a native unlit masked material."""
import hashlib
import json
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SOURCE = PROJECT / "SourceAssets" / "Candidate" / "PressShop" / "PressShop2D_Sprites_v001" / "T_LB_PS_S02_DrawForm_SpriteMasterTopdown_v003.png"
ROOT = "/Game/LineBoss/Candidates/PressShop/PressShop2DSprites_v003"
TEXTURES = ROOT + "/Textures"
MATERIALS = ROOT + "/Materials"
TEXTURE_NAME = "T_LB_PS_S02_DrawForm_SpriteMasterTopdown_v003"
MATERIAL_NAME = "M_LB_PS_S02_DrawForm_SpriteMasterTopdown_Unlit_v003"
RECEIPT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2d_s02_topdown_master_import_v003.json"
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
MEL = unreal.MaterialEditingLibrary

def fail(message):
    raise RuntimeError("PRESSSHOP_2D_S02_TOPDOWN_MASTER_IMPORT_FAIL: " + message)

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().lower()

if not SOURCE.is_file():
    fail("genuinely transparent source PNG missing")
texture_path = TEXTURES + "/" + TEXTURE_NAME
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
        fail("expected one imported texture, got {}".format(imported))
    texture = unreal.load_asset(imported[0])
if not isinstance(texture, unreal.Texture2D):
    fail("source master did not import as Texture2D")
texture.set_editor_properties({
    "srgb": True,
    "compression_settings": unreal.TextureCompressionSettings.TC_DEFAULT,
    "never_stream": True,
})
unreal.EditorAssetLibrary.save_loaded_asset(texture, only_if_is_dirty=False)
material_path = MATERIALS + "/" + MATERIAL_NAME
material = unreal.load_asset(material_path) if unreal.EditorAssetLibrary.does_asset_exist(material_path) else None
if material is None:
    material = TOOLS.create_asset(MATERIAL_NAME, MATERIALS, unreal.Material, unreal.MaterialFactoryNew())
if not isinstance(material, unreal.Material):
    fail("could not create masked material")
if hasattr(MEL, "delete_all_material_expressions"):
    MEL.delete_all_material_expressions(material)
material.set_editor_properties({
    "blend_mode": unreal.BlendMode.BLEND_MASKED,
    "shading_model": unreal.MaterialShadingModel.MSM_UNLIT,
    "two_sided": True,
    "opacity_mask_clip_value": 0.08,
})
sample = MEL.create_material_expression(material, unreal.MaterialExpressionTextureSample, -450, 0)
sample.set_editor_properties({
    "texture": texture,
    "sampler_type": unreal.MaterialSamplerType.SAMPLERTYPE_COLOR,
})
if not MEL.connect_material_property(sample, "RGB", unreal.MaterialProperty.MP_EMISSIVE_COLOR):
    fail("could not connect RGB to emissive")
if not MEL.connect_material_property(sample, "A", unreal.MaterialProperty.MP_OPACITY_MASK):
    fail("could not connect source alpha to opacity mask")
MEL.recompile_material(material)
unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
unreal.EditorAssetLibrary.save_directory(ROOT, only_if_is_dirty=False, recursive=True)
record = {
    "status": "PASS__S02_GENUINE_ALPHA_TOPDOWN_MASTER_IMPORTED__NO_MAP_TOUCHED",
    "source_png": str(SOURCE),
    "source_sha256": sha256(SOURCE),
    "texture": texture.get_path_name(),
    "material": material.get_path_name(),
    "alpha_contract": "PNG alpha drives native masked opacity; no white-key or background plate",
    "next_gate": "mount only in a fresh v006 candidate and inspect from locked game camera",
}
RECEIPT.parent.mkdir(parents=True, exist_ok=True)
RECEIPT.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_2D_S02_TOPDOWN_MASTER_IMPORT_PASS=" + json.dumps(record, sort_keys=True))

