"""Create light-invariant matte sign-face and lettering materials for train identity boards."""
from pathlib import Path
import unreal

DEST = "/Game/LineBoss/Candidates/PressShop/TrainIdentity/ReadabilityMaterials_v425"
lib = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary

def make(name, colour):
    path = f"{DEST}/{name}"
    if lib.does_asset_exist(path):
        raise RuntimeError(f"refusing to overwrite {path}")
    mat = tools.create_asset(name, DEST, unreal.Material, unreal.MaterialFactoryNew())
    if not isinstance(mat, unreal.Material):
        raise RuntimeError(f"material creation failed: {name}")
    mat.set_editor_properties({"two_sided": True, "blend_mode": unreal.BlendMode.BLEND_OPAQUE,
                               "shading_model": unreal.MaterialShadingModel.MSM_UNLIT})
    emit = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -320, 0)
    emit.set_editor_property("constant", unreal.LinearColor(*colour, 1.0))
    mel.connect_material_property(emit, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(mat)
    if not lib.save_asset(path, only_if_is_dirty=False):
        raise RuntimeError(f"save failed: {path}")
    return path

print(make("M_CA_MW_IdentityFaceCharcoal_Unlit_v425", (0.018, 0.022, 0.020)))
print(make("M_CA_MW_IdentityLetterWhite_Unlit_v425", (0.72, 0.78, 0.74)))
print("PASS__TRAIN_IDENTITY_READABILITY_MATERIALS_V425__NOT_PROMOTED")
unreal.SystemLibrary.quit_editor()
