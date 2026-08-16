"""Bind the complete packed Meshy PBR atlases for PR009/PR010."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,unreal
ROOT=Path(unreal.Paths.project_dir()).resolve();DEST='/Game/LineBoss/Candidates/PressShop/PR009_PR010_UserMeshy_v864';SRC=Path(r'C:\Users\greg_\Projects\LineBoss_Workspace\SourceAssets\Candidate\PressShop');STAGES={'PR009':SRC/r'PR009\UserMeshy_v20260809_v859\UnrealStaging_v863','PR010':SRC/r'PR010\UserMeshy_v20260809_v860\UnrealStaging_v863'}
OUT=ROOT/r'Saved\Audits\PressShopIntegration\pr009_pr010_full_pbr_v868.json';P=ROOT/r'Content\LineBoss\Maps\LB_PressShop_BuilderAuthorityCandidate_v438.umap';E='5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest().upper();before=sha(P)
if before!=E or OUT.exists():raise RuntimeError('fresh/protected invariant')
lib=unreal.EditorAssetLibrary;tools=unreal.AssetToolsHelpers.get_asset_tools();mel=unreal.MaterialEditingLibrary;rows=[]
def import_tex(src,dest,name):
 t=unreal.AssetImportTask();t.set_editor_properties({'filename':str(src),'destination_path':dest,'destination_name':name,'automated':True,'replace_existing':True,'replace_existing_settings':True,'save':True});tools.import_asset_tasks([t]);x=lib.load_asset(f'{dest}/{name}');
 if not isinstance(x,unreal.Texture2D):raise RuntimeError(name)
 return x
for station,stage in STAGES.items():
 man=json.loads((stage/f'{station}_UNREAL_STAGING_MANIFEST_v863.json').read_text(encoding='utf-8'));folder=f'{DEST}/{station}/Materials';base=lib.load_asset(f'{folder}/T_{station}_BaseColor_v864');ormrec=next(t for t in man['textures'] if t['role']=='ORM');nrec=next(t for t in man['textures'] if t['role']=='Normal');orm=import_tex(Path(ormrec['file']),folder,f'T_{station}_ORM_v868');normal=import_tex(Path(nrec['file']),folder,f'T_{station}_Normal_v868')
 orm.set_editor_properties({'srgb':False,'compression_settings':unreal.TextureCompressionSettings.TC_MASKS});normal.set_editor_properties({'srgb':False,'compression_settings':unreal.TextureCompressionSettings.TC_NORMALMAP});lib.save_loaded_asset(orm,False);lib.save_loaded_asset(normal,False)
 m=lib.load_asset(f'{folder}/M_{station}_MeshyAtlas_v864');mel.delete_all_material_expressions(m)
 b=mel.create_material_expression(m,unreal.MaterialExpressionTextureSample,-520,-100);b.texture=base;mel.connect_material_property(b,'RGB',unreal.MaterialProperty.MP_BASE_COLOR)
 o=mel.create_material_expression(m,unreal.MaterialExpressionTextureSample,-520,100);o.texture=orm;o.sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_MASKS;mel.connect_material_property(o,'G',unreal.MaterialProperty.MP_ROUGHNESS);mel.connect_material_property(o,'B',unreal.MaterialProperty.MP_METALLIC)
 n=mel.create_material_expression(m,unreal.MaterialExpressionTextureSample,-520,300);n.texture=normal;n.sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL;mel.connect_material_property(n,'RGB',unreal.MaterialProperty.MP_NORMAL)
 mel.recompile_material(m);lib.save_loaded_asset(m,False);rows.append({'station':station,'material':m.get_path_name(),'base':base.get_path_name(),'orm':orm.get_path_name(),'normal':normal.get_path_name(),'mapping':'ORM G=roughness B=metallic'})
after=sha(P)
if after!=before:raise RuntimeError('protected changed')
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps({'status':'PASS_FULL_MESHY_PBR_BINDING__RECAPTURE_REQUIRED','generated_utc':datetime.now(timezone.utc).isoformat(),'records':rows,'protected_v438_before':before,'protected_v438_after':after},indent=2),encoding='utf-8');unreal.log('LINE_BOSS_PR009_PR010_PBR_V868_PASS')
