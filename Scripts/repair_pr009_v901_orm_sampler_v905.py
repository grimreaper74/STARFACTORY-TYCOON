from pathlib import Path
import hashlib,unreal
R=Path(unreal.Paths.project_dir()).resolve();P=R/r'Content\LineBoss\Maps\LB_PressShop_BuilderAuthorityCandidate_v438.umap';E='5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest().upper();b=sha(P)
if b!=E:raise RuntimeError('protected invariant')
lib=unreal.EditorAssetLibrary;mat=lib.load_asset('/Game/LineBoss/Candidates/PressShop/PR009_OriginalFBX_v901/Materials/M_PR009_OriginalPBR_v901');orm=lib.load_asset('/Game/LineBoss/Candidates/PressShop/PR009_OriginalFBX_v901/Materials/T_PR009_ORM_v883')
found=0
for e in unreal.MaterialEditingLibrary.get_material_expressions(mat):
 if isinstance(e,unreal.MaterialExpressionTextureSample) and e.get_editor_property('texture')==orm:e.set_editor_property('sampler_type',unreal.MaterialSamplerType.SAMPLERTYPE_MASKS);found+=1
if found!=1:raise RuntimeError(f'ORM samples {found}')
unreal.MaterialEditingLibrary.recompile_material(mat);lib.save_asset(mat.get_path_name(),False)
if sha(P)!=b:raise RuntimeError('protected changed')
unreal.log('LINE_BOSS_PR009_V901_ORM_SAMPLER_V905_PASS')
