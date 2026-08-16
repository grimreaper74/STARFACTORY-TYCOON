import unreal

DEST = '/Game/LineBoss/Candidates/PressShop/PR009_OriginalFBX_v901'
FOLDER = DEST + '/Materials'
MESH_PATH = DEST + '/SM_CA_MW_PR009_OriginalHighPoly_v883'
BASE_PATH = FOLDER + '/T_PR009_BaseColor_v883'
NORMAL_PATH = FOLDER + '/T_PR009_Normal_v883'
MAT_PATH = FOLDER + '/M_PR009_SafePBR_v907'

lib = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary

mesh = lib.load_asset(MESH_PATH)
base = lib.load_asset(BASE_PATH)
normal = lib.load_asset(NORMAL_PATH)
if not mesh or not base or not normal:
    raise RuntimeError('PR009 mesh or textures missing')

if lib.does_asset_exist(MAT_PATH):
    lib.delete_asset(MAT_PATH)
mat = tools.create_asset('M_PR009_SafePBR_v907', FOLDER, unreal.Material, unreal.MaterialFactoryNew())

b = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -500, -100)
b.texture = base
b.sampler_type = unreal.MaterialSamplerType.SAMPLERTYPE_COLOR
mel.connect_material_property(b, 'RGB', unreal.MaterialProperty.MP_BASE_COLOR)

n = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -500, 220)
n.texture = normal
n.sampler_type = unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL
mel.connect_material_property(n, 'RGB', unreal.MaterialProperty.MP_NORMAL)

rough = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -300, 60)
rough.r = 0.48
mel.connect_material_property(rough, '', unreal.MaterialProperty.MP_ROUGHNESS)

metal = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -300, 130)
metal.r = 0.35
mel.connect_material_property(metal, '', unreal.MaterialProperty.MP_METALLIC)

mat.set_editor_property('two_sided', False)
mel.recompile_material(mat)
lib.save_asset(MAT_PATH, False)
mesh.set_material(0, mat)
lib.save_asset(MESH_PATH, False)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.log('LINE_BOSS_PR009_SAFE_MATERIAL_V907_PASS')
