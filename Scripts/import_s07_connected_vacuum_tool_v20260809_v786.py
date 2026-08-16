from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
DEST='/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v786/S07ConnectedVacuumTool'
SOURCE=Path(r'C:\Users\greg_\Projects\LineBoss_Workspace\SourceAssets\Candidate\PressTrains\Shared\S07UnloadRobotUserRuntime_v785\Cairnwell_S07_UnloadRobot_ConnectedVacuumTool_v785.glb')
OUT=ROOT/'Saved/Audits/PressShopIntegration/s07_connected_vacuum_tool_intake_v20260809_v786.json'
PROTECTED=ROOT/'Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap'
EXPECTED='5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8'
sha=lambda:hashlib.sha256(PROTECTED.read_bytes()).hexdigest().upper()
lib=unreal.EditorAssetLibrary
if sha()!=EXPECTED:raise RuntimeError('Protected v438 mismatch')
if not SOURCE.exists():raise RuntimeError(f'Missing source {SOURCE}')
if OUT.exists() or (lib.does_directory_exist(DEST) and lib.list_assets(DEST,recursive=True,include_folder=False)):raise RuntimeError('Refusing overwrite v786')

task=unreal.AssetImportTask()
task.set_editor_properties({'filename':str(SOURCE),'destination_path':DEST,'automated':True,'replace_existing':False,'replace_existing_settings':False,'save':True})
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
assets=lib.list_assets(DEST,recursive=True,include_folder=False)
meshes=[];materials=[];textures=[];mesh_records=[]
for path in assets:
    asset=unreal.load_asset(path)
    if isinstance(asset,unreal.StaticMesh):
        meshes.append(path)
        bounds=asset.get_bounds();extent=bounds.box_extent
        mesh_records.append({'path':path,'extent_cm':[extent.x,extent.y,extent.z],'material_slots':asset.get_num_sections(0)})
    elif isinstance(asset,unreal.MaterialInterface):materials.append(path)
    elif isinstance(asset,unreal.Texture):textures.append(path)
required=['BASE_STATIC','TURNTABLE','LOWER_ARM','UPPER_ARM','WRIST','VACUUM_TOOL'];failures=[]
if len(meshes)!=6:failures.append(f'static mesh count {len(meshes)} expected 6')
for fragment in required:
    if not any(fragment.lower() in path.lower() for path in meshes):failures.append('missing '+fragment)
if not materials:failures.append('no imported materials')
if not textures:failures.append('no imported textures')
tool_record=next((record for record in mesh_records if 'vacuum_tool' in record['path'].lower()),None)
if tool_record is None:failures.append('vacuum tool inspection missing')
elif tool_record['material_slots']<2:failures.append('vacuum tool lost separate worked-steel spreader material')
if sha()!=EXPECTED:failures.append('protected hash changed')
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps({'revision':'v786','generated_utc':datetime.now(timezone.utc).isoformat(),'status':'PASS__S07_V785_SIX_COMPONENT_TEXTURED_INTAKE__SPREADER_MATERIAL_RETAINED__MAP_PLACEMENT_REQUIRED' if not failures else 'FAIL__S07_V786_INTAKE','destination':DEST,'source':str(SOURCE),'static_meshes':mesh_records,'materials':materials,'textures':textures,'vacuum_tool':tool_record,'failures':failures,'protected_sha256':sha(),'meshy_credits_used_by_codex':0},indent=2),encoding='utf-8')
if failures:raise RuntimeError('; '.join(failures))
unreal.log('LINE_BOSS_S07_CONNECTED_VACUUM_TOOL_INTAKE_V786_PASS')
