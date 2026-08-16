"""Persistent single-asset import gate for untouched PR009 original."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,unreal
ROOT=Path(unreal.Paths.project_dir()).resolve();DEST='/Game/LineBoss/Candidates/PressShop/PR009_OriginalFBX_v901';STAGE=Path(r'C:\Users\greg_\Projects\LineBoss_Workspace\SourceAssets\Candidate\PressShop\PR009\UserMeshy_v20260809_v859\UnrealStaging_OriginalFBX_v883');P=ROOT/r'Content\LineBoss\Maps\LB_PressShop_BuilderAuthorityCandidate_v438.umap';E='5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest().upper();before=sha(P)
if before!=E or unreal.EditorAssetLibrary.does_directory_exist(DEST):raise RuntimeError('protected/fresh invariant')
lib=unreal.EditorAssetLibrary;tools=unreal.AssetToolsHelpers.get_asset_tools();mel=unreal.MaterialEditingLibrary
unreal.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
def imp(src,dest,name,mesh=False):
 t=unreal.AssetImportTask();t.set_editor_properties({'filename':str(src),'destination_path':dest,'destination_name':name,'automated':True,'replace_existing':False,'save':True})
 if mesh:
  ui=unreal.FbxImportUI();ui.set_editor_properties({'import_mesh':True,'import_as_skeletal':False,'import_materials':False,'import_textures':False,'mesh_type_to_import':unreal.FBXImportType.FBXIT_STATIC_MESH,'automated_import_should_detect_type':False});ui.static_mesh_import_data.set_editor_properties({'combine_meshes':True,'generate_lightmap_u_vs':False,'auto_generate_collision':False,'import_uniform_scale':100.0,'normal_import_method':unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS});t.options=ui
 tools.import_asset_tasks([t]);unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation();a=lib.load_asset(f'{dest}/{name}');
 if not a:raise RuntimeError(f'import {name}')
 lib.save_asset(a.get_path_name(),False);return a
man=json.loads(next(STAGE.glob('*MANIFEST*.json')).read_text(encoding='utf-8'));mesh_file=Path(man['fbx']);mesh=imp(mesh_file,DEST,mesh_file.stem,True);folder=f'{DEST}/Materials';tex={}
for r in man['textures']:
 x=imp(Path(r['file']),folder,Path(r['file']).stem);role=r['role'];tex[role]=x
 if role=='BaseColor':x.set_editor_property('srgb',True)
 elif role=='ORM':x.set_editor_property('srgb',False);x.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_MASKS)
 else:x.set_editor_property('srgb',False);x.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_NORMALMAP)
 lib.save_asset(x.get_path_name(),False)
mat=tools.create_asset('M_PR009_OriginalPBR_v901',folder,unreal.Material,unreal.MaterialFactoryNew());b=mel.create_material_expression(mat,unreal.MaterialExpressionTextureSample,-500,-120);b.texture=tex['BaseColor'];mel.connect_material_property(b,'RGB',unreal.MaterialProperty.MP_BASE_COLOR);o=mel.create_material_expression(mat,unreal.MaterialExpressionTextureSample,-500,100);o.texture=tex['ORM'];mel.connect_material_property(o,'G',unreal.MaterialProperty.MP_ROUGHNESS);mel.connect_material_property(o,'B',unreal.MaterialProperty.MP_METALLIC);n=mel.create_material_expression(mat,unreal.MaterialExpressionTextureSample,-500,300);n.texture=tex['Normal'];n.sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL;mel.connect_material_property(n,'RGB',unreal.MaterialProperty.MP_NORMAL);mat.set_editor_property('two_sided',False);mel.recompile_material(mat);lib.save_asset(mat.get_path_name(),False);mesh.set_material(0,mat);ns=mesh.get_editor_property('nanite_settings');ns.enabled=True;mesh.set_editor_property('nanite_settings',ns);lib.save_asset(mesh.get_path_name(),False)
d=mesh.get_bounds().box_extent*2;bounds=[d.x,d.y,d.z]
if max(abs(v-e) for v,e in zip(bounds,[520,760,425]))>=2:raise RuntimeError(bounds)
if sha(P)!=before:raise RuntimeError('protected changed')
out=ROOT/r'Saved\Audits\PressShopIntegration\pr009_original_fbx_persistent_import_v901.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps({'generated_utc':datetime.now(timezone.utc).isoformat(),'status':'PASS_IMPORT__FILESYSTEM_PERSISTENCE_RECHECK_AFTER_EXIT_REQUIRED','mesh':mesh.get_path_name(),'material':mat.get_path_name(),'bounds_cm':bounds,'polygons':man['polygons'],'topology_changes':0,'protected_v438':before,'meshy_credits_used':0},indent=2),encoding='utf-8');unreal.log('LINE_BOSS_PR009_ORIGINAL_FBX_PERSISTENT_V901_PASS')
