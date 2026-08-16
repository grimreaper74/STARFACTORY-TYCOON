"""Untouched high-poly FBX visual gate for PR009/PR010. Isolated; never touches v438/v791."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
MAP='/Game/LineBoss/Maps/LB_PressShop_PR009_PR010_OriginalFBX_Isolated_v884'
DEST='/Game/LineBoss/Candidates/PressShop/PR009_PR010_OriginalFBX_v884'
SRC=Path(r'C:\Users\greg_\Projects\LineBoss_Workspace\SourceAssets\Candidate\PressShop')
STAGES={
 'PR009':SRC/r'PR009\UserMeshy_v20260809_v859\UnrealStaging_OriginalFBX_v883',
 'PR010':SRC/r'PR010\UserMeshy_v20260809_v860\UnrealStaging_OriginalFBX_v883',
}
OUT=ROOT/r'Saved\Audits\PressShopIntegration\pr009_pr010_original_fbx_isolated_intake_v884.json'
PROTECTED=ROOT/r'Content\LineBoss\Maps\LB_PressShop_BuilderAuthorityCandidate_v438.umap'
EXPECTED='5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
before=sha(PROTECTED)
if before!=EXPECTED or unreal.EditorAssetLibrary.does_asset_exist(MAP) or OUT.exists(): raise RuntimeError('fresh/protected invariant')
lib=unreal.EditorAssetLibrary; at=unreal.AssetToolsHelpers.get_asset_tools(); mel=unreal.MaterialEditingLibrary
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
unreal.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')

def import_file(src,dest,name,mesh=False):
 t=unreal.AssetImportTask(); t.set_editor_properties({'filename':str(src),'destination_path':dest,'destination_name':name,'automated':True,'replace_existing':True,'replace_existing_settings':True,'save':True})
 if mesh:
  ui=unreal.FbxImportUI(); ui.set_editor_properties({'import_mesh':True,'import_as_skeletal':False,'import_materials':False,'import_textures':False,'mesh_type_to_import':unreal.FBXImportType.FBXIT_STATIC_MESH,'automated_import_should_detect_type':False})
  ui.static_mesh_import_data.set_editor_properties({'combine_meshes':True,'generate_lightmap_u_vs':False,'auto_generate_collision':False,'import_uniform_scale':100.0,'normal_import_method':unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS})
  t.options=ui
 at.import_asset_tasks([t]); unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation(); return lib.load_asset(f'{dest}/{name}')

def texture(src,folder,name,role):
 x=import_file(src,folder,name)
 if role=='BaseColor': x.set_editor_property('srgb',True)
 elif role=='ORM': x.set_editor_property('srgb',False); x.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_MASKS)
 else: x.set_editor_property('srgb',False); x.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_NORMALMAP)
 x.update_resource(); lib.save_loaded_asset(x,False); return x

def material(station,folder,base,orm,normal):
 m=at.create_asset(f'M_{station}_OriginalPBR_v884',folder,unreal.Material,unreal.MaterialFactoryNew())
 b=mel.create_material_expression(m,unreal.MaterialExpressionTextureSample,-500,-120); b.texture=base; mel.connect_material_property(b,'RGB',unreal.MaterialProperty.MP_BASE_COLOR)
 o=mel.create_material_expression(m,unreal.MaterialExpressionTextureSample,-500,100); o.texture=orm
 mel.connect_material_property(o,'G',unreal.MaterialProperty.MP_ROUGHNESS); mel.connect_material_property(o,'B',unreal.MaterialProperty.MP_METALLIC)
 n=mel.create_material_expression(m,unreal.MaterialExpressionTextureSample,-500,300); n.texture=normal; n.sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL
 mel.connect_material_property(n,'RGB',unreal.MaterialProperty.MP_NORMAL)
 mel.recompile_material(m); lib.save_loaded_asset(m,False); return m

records={}
for station,stage in STAGES.items():
 man=json.loads(next(stage.glob('*MANIFEST*.json')).read_text(encoding='utf-8'))
 folder=f'{DEST}/{station}'; mf=Path(man['fbx']); mesh=import_file(mf,folder,mf.stem,True)
 tex={r['role']:texture(Path(r['file']),f'{folder}/Materials',Path(r['file']).stem,r['role']) for r in man['textures']}
 mat=material(station,f'{folder}/Materials',tex['BaseColor'],tex['ORM'],tex['Normal']); mesh.set_material(0,mat)
 try:
  ns=mesh.get_editor_property('nanite_settings'); ns.enabled=True; mesh.set_editor_property('nanite_settings',ns)
 except Exception as e: unreal.log_warning(f'Nanite setting deferred: {e}')
 lib.save_loaded_asset(mesh,False); d=mesh.get_bounds().box_extent*2; target={'PR009':[520,760,425],'PR010':[1400,840,360]}[station]
 records[station]={'mesh':mesh.get_path_name(),'material':mat.get_path_name(),'bounds_cm':[d.x,d.y,d.z],'target_cm':target,'bounds_pass':max(abs(v-e) for v,e in zip((d.x,d.y,d.z),target))<2,'polygons':man['polygons'],'topology_changes':man['topology_changes']}
 if not records[station]['bounds_pass']: raise RuntimeError(f'{station} bounds {records[station]}')

if not levels.new_level(MAP): raise RuntimeError('map create')
for station,loc in {'PR009':(-650,0,0),'PR010':(650,0,0)}.items():
 a=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(*loc),unreal.Rotator()); a.set_actor_label(f'LB_{station}_OriginalHighPoly_v884'); a.static_mesh_component.set_static_mesh(lib.load_asset(records[station]['mesh'])); a.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION); a.tags=[unreal.Name(f'LB.Station.{station}'),unreal.Name('LB.IsolatedValidation.v884')]
if not levels.save_current_level(): raise RuntimeError('save')
after=sha(PROTECTED)
if after!=before: raise RuntimeError('protected changed')
map_file=ROOT/r'Content\LineBoss\Maps\LB_PressShop_PR009_PR010_OriginalFBX_Isolated_v884.umap'
payload={'status':'PASS_ISOLATED_IMPORT__VISUAL_REVIEW_REQUIRED__NOT_PROMOTED','generated_utc':datetime.now(timezone.utc).isoformat(),'map':MAP,'map_sha256':sha(map_file),'records':records,'protected_v438_before':before,'protected_v438_after':after,'meshy_credits_used':0}
OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8'); unreal.log('LINE_BOSS_PR009_PR010_ORIGINAL_FBX_V884_PASS')
