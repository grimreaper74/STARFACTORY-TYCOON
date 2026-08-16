"""Create isolated two-sided PBR lettering material for physical train signs."""
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir())
DEST="/Game/LineBoss/Candidates/PressShop/TrainIdentity/ReleaseMaterials_v414"
NAME="M_CA_MW_IdentityLetterWhite_TwoSided_v414"
PATH=DEST+"/"+NAME
lib=unreal.EditorAssetLibrary
if lib.does_asset_exist(PATH):raise RuntimeError("refusing to overwrite v414")
tools=unreal.AssetToolsHelpers.get_asset_tools();mel=unreal.MaterialEditingLibrary
mat=tools.create_asset(NAME,DEST,unreal.Material,unreal.MaterialFactoryNew())
if not isinstance(mat,unreal.Material):raise RuntimeError("material creation failed")
mat.set_editor_properties({"two_sided":True,"blend_mode":unreal.BlendMode.BLEND_OPAQUE})
base=mel.create_material_expression(mat,unreal.MaterialExpressionConstant3Vector,-420,0);base.set_editor_property("constant",unreal.LinearColor(0.78,0.86,0.82,1))
rough=mel.create_material_expression(mat,unreal.MaterialExpressionConstant,-420,140);rough.set_editor_property("r",0.34)
metal=mel.create_material_expression(mat,unreal.MaterialExpressionConstant,-420,250);metal.set_editor_property("r",0.08)
mel.connect_material_property(base,"",unreal.MaterialProperty.MP_BASE_COLOR);mel.connect_material_property(rough,"",unreal.MaterialProperty.MP_ROUGHNESS);mel.connect_material_property(metal,"",unreal.MaterialProperty.MP_METALLIC)
mel.recompile_material(mat)
if not lib.save_asset(PATH,only_if_is_dirty=False):raise RuntimeError("material save failed")
print("PASS__TWO_SIDED_IDENTITY_LETTER_MATERIAL_V414__NOT_PROMOTED")
unreal.SystemLibrary.quit_editor()
