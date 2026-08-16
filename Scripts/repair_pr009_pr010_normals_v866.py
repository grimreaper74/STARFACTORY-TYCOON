"""Reimport PR009/PR010 with UE-computed smooth MikkTSpace normals."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,unreal
ROOT=Path(unreal.Paths.project_dir()).resolve();DEST='/Game/LineBoss/Candidates/PressShop/PR009_PR010_UserMeshy_v864';SRC=Path(r'C:\Users\greg_\Projects\LineBoss_Workspace\SourceAssets\Candidate\PressShop')
STAGES={'PR009':SRC/r'PR009\UserMeshy_v20260809_v859\UnrealStaging_v871','PR010':SRC/r'PR010\UserMeshy_v20260809_v860\UnrealStaging_v863'}
OUT=ROOT/r'Saved\Audits\PressShopIntegration\pr009_flow_axis_normals_repair_v872.json';P=ROOT/r'Content\LineBoss\Maps\LB_PressShop_BuilderAuthorityCandidate_v438.umap';E='5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest().upper();before=sha(P)
if before!=E or OUT.exists():raise RuntimeError('fresh/protected invariant')
lib=unreal.EditorAssetLibrary;tools=unreal.AssetToolsHelpers.get_asset_tools();unreal.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0');rows=[]
for station,stage in STAGES.items():
 man_name=f'{station}_UNREAL_STAGING_MANIFEST_{"v871" if station=="PR009" else "v863"}.json';man=json.loads((stage/man_name).read_text(encoding='utf-8'));src=Path(man['visual_fbx']);folder=f'{DEST}/{station}';name=src.stem;mat=lib.load_asset(f'{folder}/Materials/M_{station}_MeshyAtlas_v864')
 t=unreal.AssetImportTask();t.set_editor_properties({'filename':str(src),'destination_path':folder,'destination_name':name,'automated':True,'replace_existing':True,'replace_existing_settings':True,'save':True})
 ui=unreal.FbxImportUI();ui.set_editor_properties({'import_mesh':True,'import_as_skeletal':False,'import_materials':False,'import_textures':False,'mesh_type_to_import':unreal.FBXImportType.FBXIT_STATIC_MESH,'automated_import_should_detect_type':False})
 ui.static_mesh_import_data.set_editor_properties({'combine_meshes':True,'generate_lightmap_u_vs':True,'auto_generate_collision':False,'import_uniform_scale':100.0,'normal_import_method':unreal.FBXNormalImportMethod.FBXNIM_COMPUTE_NORMALS,'normal_generation_method':unreal.FBXNormalGenerationMethod.MIKK_T_SPACE,'remove_degenerates':True})
 t.options=ui;tools.import_asset_tasks([t]);unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation();mesh=lib.load_asset(f'{folder}/{name}')
 if not isinstance(mesh,unreal.StaticMesh):raise RuntimeError(station)
 mesh.set_material(0,mat);lib.save_loaded_asset(mesh,False);d=mesh.get_bounds().box_extent*2;rows.append({'station':station,'mesh':mesh.get_path_name(),'bounds_cm':[d.x,d.y,d.z],'normal_method':'COMPUTE_NORMALS_MIKKTSPACE','material':mat.get_path_name()})
after=sha(P)
if after!=before:raise RuntimeError('protected changed')
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps({'status':'PASS_REIMPORT_COMPUTED_NORMALS__RECAPTURE_REQUIRED','generated_utc':datetime.now(timezone.utc).isoformat(),'records':rows,'protected_v438_before':before,'protected_v438_after':after},indent=2),encoding='utf-8');unreal.log('LINE_BOSS_PR009_PR010_NORMALS_V866_PASS')
