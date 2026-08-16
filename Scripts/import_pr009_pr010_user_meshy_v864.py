"""Isolated intake of user-supplied PR009/PR010; never touches v438 or v791."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
MAP='/Game/LineBoss/Maps/LB_PressShop_PR009_PR010_UserMeshy_Isolated_v864'
DEST='/Game/LineBoss/Candidates/PressShop/PR009_PR010_UserMeshy_v864'
SRC=Path(r'C:\Users\greg_\Projects\LineBoss_Workspace\SourceAssets\Candidate\PressShop')
STAGES={
 'PR009':SRC/r'PR009\UserMeshy_v20260809_v859\UnrealStaging_v863',
 'PR010':SRC/r'PR010\UserMeshy_v20260809_v860\UnrealStaging_v863',
}
OUT=ROOT/r'Saved\Audits\PressShopIntegration\pr009_pr010_user_meshy_isolated_intake_v864.json'
PROTECTED=ROOT/r'Content\LineBoss\Maps\LB_PressShop_BuilderAuthorityCandidate_v438.umap'
EXPECTED='5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
before=sha(PROTECTED)
if before!=EXPECTED or unreal.EditorAssetLibrary.does_asset_exist(MAP) or OUT.exists():raise RuntimeError('fresh/protected invariant')
lib=unreal.EditorAssetLibrary; tools=unreal.AssetToolsHelpers.get_asset_tools(); mel=unreal.MaterialEditingLibrary
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
unreal.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')

def import_file(src,dest,name,mesh=False):
 t=unreal.AssetImportTask(); t.set_editor_properties({'filename':str(src),'destination_path':dest,'destination_name':name,'automated':True,'replace_existing':True,'replace_existing_settings':True,'save':True})
 if mesh:
  ui=unreal.FbxImportUI(); ui.set_editor_properties({'import_mesh':True,'import_as_skeletal':False,'import_materials':False,'import_textures':False,'mesh_type_to_import':unreal.FBXImportType.FBXIT_STATIC_MESH,'automated_import_should_detect_type':False})
  ui.static_mesh_import_data.set_editor_properties({'combine_meshes':True,'generate_lightmap_u_vs':True,'auto_generate_collision':False,'import_uniform_scale':100.0}); t.options=ui
 tools.import_asset_tasks([t]); unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation(); return lib.load_asset(f'{dest}/{name}')

def make_material(station,base):
 folder=f'{DEST}/{station}/Materials'; name=f'M_{station}_MeshyAtlas_v864'; m=tools.create_asset(name,folder,unreal.Material,unreal.MaterialFactoryNew())
 b=mel.create_material_expression(m,unreal.MaterialExpressionTextureSample,-350,-60); b.texture=base; mel.connect_material_property(b,'RGB',unreal.MaterialProperty.MP_BASE_COLOR)
 r=mel.create_material_expression(m,unreal.MaterialExpressionConstant,-150,100); r.r=.54; mel.connect_material_property(r,'',unreal.MaterialProperty.MP_ROUGHNESS)
 mt=mel.create_material_expression(m,unreal.MaterialExpressionConstant,-150,180); mt.r=.12; mel.connect_material_property(mt,'',unreal.MaterialProperty.MP_METALLIC)
 mel.recompile_material(m); lib.save_loaded_asset(m,False); return m

records={}
for station,stage in STAGES.items():
 man=json.loads((stage/f'{station}_UNREAL_STAGING_MANIFEST_v863.json').read_text(encoding='utf-8'))
 folder=f'{DEST}/{station}'; mesh_name=Path(man['visual_fbx']).stem
 mesh=import_file(Path(man['visual_fbx']),folder,mesh_name,True)
 if not isinstance(mesh,unreal.StaticMesh):raise RuntimeError(f'{station} mesh import')
 base_rec=next(t for t in man['textures'] if t['role']=='BaseColor'); tex=import_file(Path(base_rec['file']),f'{folder}/Materials',f'T_{station}_BaseColor_v864')
 if not isinstance(tex,unreal.Texture2D):raise RuntimeError(f'{station} base texture import')
 mat=make_material(station,tex); mesh.set_material(0,mat); lib.save_loaded_asset(mesh,False)
 d=mesh.get_bounds().box_extent*2
 target={'PR009':[760,520,425],'PR010':[1400,840,360]}[station]
 delta=[abs(v-e) for v,e in zip((d.x,d.y,d.z),target)]
 records[station]={'mesh':mesh.get_path_name(),'material':mat.get_path_name(),'bounds_cm':[d.x,d.y,d.z],'target_cm':target,'bounds_pass':max(delta)<2.0,'polygons':man['polygons'],'proxy_count':len(man['proxies']),'socket_count':len(man['sockets'])}
 if not records[station]['bounds_pass']:raise RuntimeError(f'{station} bounds {records[station]}')

if not levels.new_level(MAP):raise RuntimeError('map create')
placements={'PR009':(-650,0,0),'PR010':(650,0,0)}
for station,loc in placements.items():
 mesh=lib.load_asset(records[station]['mesh']); a=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(*loc),unreal.Rotator()); a.set_actor_label(f'LB_{station}_UserMeshyVisual_v864'); a.static_mesh_component.set_static_mesh(mesh); a.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION); a.tags=[unreal.Name(f'LB.Station.{station}'),unreal.Name('LB.Asset.NewApproved'),unreal.Name('LB.IsolatedValidation.v864')]
 # One conservative separate proxy per station; detailed route blockers remain authored from manifest after review.
 dims=records[station]['target_cm']; p=actors.spawn_actor_from_class(unreal.BlockingVolume,unreal.Vector(loc[0],loc[1],dims[2]/2),unreal.Rotator()); p.set_actor_label(f'LB_{station}_ProtectedEnvelopeProxy_v864'); p.set_actor_scale3d(unreal.Vector(dims[0]/200,dims[1]/200,dims[2]/200)); p.tags=[unreal.Name('LB.Collision.Proxy'),unreal.Name(f'LB.Station.{station}')]
if not levels.save_current_level():raise RuntimeError('save')
after=sha(PROTECTED)
if after!=before:raise RuntimeError('protected changed')
map_file=ROOT/r'Content\LineBoss\Maps\LB_PressShop_PR009_PR010_UserMeshy_Isolated_v864.umap'
payload={'status':'PASS_ISOLATED_IMPORT_BOUNDS_AND_MATERIALS__VISUAL_REVIEW_REQUIRED__NOT_PROMOTED','generated_utc':datetime.now(timezone.utc).isoformat(),'map':MAP,'map_sha256':sha(map_file),'records':records,'protected_v438_before':before,'protected_v438_after':after,'meshy_credits_used':0}
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8');unreal.log('LINE_BOSS_PR009_PR010_USERMESHY_V864_PASS')
