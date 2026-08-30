"""Import the high-overhead S02 master and build a native white-key material.

The source plate is intentionally flat studio-white because the image generator did
not preserve alpha on the high-camera pass. Unreal removes only near-white pixels
in all three channels. The conservative 0.93 linear threshold clears the studio
plate while retaining the warm-white machine panels (whose blue channel is lower).
"""
import hashlib
import json
from pathlib import Path

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SOURCE = PROJECT / "SourceAssets" / "Candidate" / "PressShop" / "PressShop2D_Sprites_v001" / "T_LB_PS_S02_DrawForm_SpriteMasterOverhead_Keyed_v002.png"
ROOT = "/Game/LineBoss/Candidates/PressShop/PressShop2DSprites_v002"
TEXTURES = ROOT + "/Textures"
MATERIALS = ROOT + "/Materials"
TEXTURE_NAME = "T_LB_PS_S02_DrawForm_SpriteMasterOverhead_Keyed_v002"
MATERIAL_NAME = "M_LB_PS_S02_DrawForm_SpriteMasterOverhead_Keyed_Unlit_v002"
RECEIPT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2d_s02_overhead_master_import_v002.json"
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
MEL = unreal.MaterialEditingLibrary

def fail(message):
    raise RuntimeError("PRESSSHOP_2D_S02_OVERHEAD_MASTER_IMPORT_FAIL: " + message)

def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def create(material, kind, x, y):
    return MEL.create_material_expression(material, kind, x, y)

def scalar(material, value, x, y):
    node = create(material, unreal.MaterialExpressionConstant, x, y)
    node.set_editor_property("r", value)
    return node

def channel_mask(material, sample, channel, x, y):
    node = create(material, unreal.MaterialExpressionComponentMask, x, y)
    node.set_editor_property(channel.lower(), True)
    MEL.connect_material_expressions(sample, "RGB", node, "")
    return node

def white_channel_key(material, channel, x, y):
    test = create(material, unreal.MaterialExpressionIf, x, y)
    MEL.connect_material_expressions(channel, "", test, "A")
    # Imported texture samples can fall just below 1.0 after the native texture
    # pipeline, so 0.997 left a visible white rectangle. 0.93 still requires all
    # three channels to be near white and therefore does not key cream/yellow art.
    threshold = scalar(material, 0.93, x - 160, y + 90)
    zero = scalar(material, 0.0, x - 160, y + 170)
    one = scalar(material, 1.0, x - 160, y + 250)
    MEL.connect_material_expressions(threshold, "", test, "B")
    # These are Unreal's actual editor-facing pin labels, verified by
    # audit_pressshop_if_pins_v001.py. C++ member names do not work here.
    if not MEL.connect_material_expressions(zero, "", test, "A > B"):
        fail("could not connect If.A > B")
    if not MEL.connect_material_expressions(zero, "", test, "A == B"):
        fail("could not connect If.A == B")
    if not MEL.connect_material_expressions(one, "", test, "A < B"):
        fail("could not connect If.A < B")
    return test

if not SOURCE.is_file():
    fail("overhead source plate is missing")
texture_path = TEXTURES + "/" + TEXTURE_NAME
texture = unreal.load_asset(texture_path) if unreal.EditorAssetLibrary.does_asset_exist(texture_path) else None
if texture is None:
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(SOURCE), "destination_path": TEXTURES,
        "destination_name": TEXTURE_NAME, "automated": True,
        "replace_existing": False, "save": True,
    })
    TOOLS.import_asset_tasks([task])
    imported = list(task.get_editor_property("imported_object_paths") or [])
    if len(imported) != 1:
        fail("expected exactly one source plate import, got {}".format(imported))
    texture = unreal.load_asset(imported[0])
if not isinstance(texture, unreal.Texture2D):
    fail("source plate did not import as Texture2D")
texture.set_editor_property("srgb", True)
texture.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_DEFAULT)
texture.set_editor_property("never_stream", True)
unreal.EditorAssetLibrary.save_loaded_asset(texture, only_if_is_dirty=False)

material_path = MATERIALS + "/" + MATERIAL_NAME
material = unreal.load_asset(material_path) if unreal.EditorAssetLibrary.does_asset_exist(material_path) else None
if material is None:
    material = TOOLS.create_asset(MATERIAL_NAME, MATERIALS, unreal.Material, unreal.MaterialFactoryNew())
if not isinstance(material, unreal.Material):
    fail("could not create overhead master material")
if hasattr(MEL, "delete_all_material_expressions"):
    MEL.delete_all_material_expressions(material)
material.set_editor_properties({
    "blend_mode": unreal.BlendMode.BLEND_MASKED,
    "shading_model": unreal.MaterialShadingModel.MSM_UNLIT,
    "two_sided": True,
    "opacity_mask_clip_value": 0.08,
})
sample = create(material, unreal.MaterialExpressionTextureSample, -780, 0)
sample.set_editor_properties({"texture": texture, "sampler_type": unreal.MaterialSamplerType.SAMPLERTYPE_COLOR})
MEL.connect_material_property(sample, "RGB", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
red = white_channel_key(material, channel_mask(material, sample, "R", -610, 150), -370, 150)
green = white_channel_key(material, channel_mask(material, sample, "G", -610, 390), -370, 390)
blue = white_channel_key(material, channel_mask(material, sample, "B", -610, 630), -370, 630)
rg = create(material, unreal.MaterialExpressionMultiply, -90, 270)
MEL.connect_material_expressions(red, "", rg, "A")
MEL.connect_material_expressions(green, "", rg, "B")
rgb = create(material, unreal.MaterialExpressionMultiply, 120, 310)
MEL.connect_material_expressions(rg, "", rgb, "A")
MEL.connect_material_expressions(blue, "", rgb, "B")
if not MEL.connect_material_property(rgb, "", unreal.MaterialProperty.MP_OPACITY_MASK):
    fail("could not connect opacity mask output")
MEL.recompile_material(material)
unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
unreal.EditorAssetLibrary.save_directory(ROOT, only_if_is_dirty=False, recursive=True)

receipt = {
    "status": "PASS__S02_OVERHEAD_MASTER_IMPORTED_WITH_NATIVE_THREE_CHANNEL_WHITE_KEY__NO_MAP_TOUCHED",
    "map_loaded": False,
    "map_saved": False,
    "source_png": str(SOURCE),
    "source_sha256": sha256(SOURCE),
    "texture": texture.get_path_name(),
    "material": material.get_path_name(),
    "key_rule": "only RGB channels all greater than 0.93 become opacity 0; cream panels remain visible because their blue channel is lower",
    "next_gate": "mount in a fresh candidate map clone and inspect the fixed overview capture",
}
RECEIPT.parent.mkdir(parents=True, exist_ok=True)
RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_2D_S02_OVERHEAD_MASTER_IMPORT_PASS=" + json.dumps(receipt, sort_keys=True))
