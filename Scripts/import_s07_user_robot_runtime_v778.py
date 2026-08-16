from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, unreal

ROOT=Path(unreal.Paths.project_dir())
DEST='/Game/LineBoss/Developer/Validation/PressTrains/S07UserRobotRuntime_v778'
SOURCE=Path(r'C:\Users\greg_\Projects\LineBoss_Workspace\SourceAssets\Candidate\PressTrains\Shared\S07UnloadRobotUserRuntime_v776\Cairnwell_S07_UnloadRobot_Movable_v776.glb')
OUT=ROOT/'Saved/Audits/PressShopIntegration/s07_user_robot_intake_v778.json'
PROTECTED=ROOT/'Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap'
EXPECTED='5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8'
sha=lambda:hashlib.sha256(PROTECTED.read_bytes()).hexdigest().upper();lib=unreal.EditorAssetLibrary
if sha()!=EXPECTED:raise RuntimeError('Protected v438 mismatch')
if not SOURCE.exists():raise RuntimeError(f'Missing source {SOURCE}')
if OUT.exists() or (lib.does_directory_exist(DEST) and lib.list_assets(DEST,recursive=True,include_folder=False)):raise RuntimeError('Refusing overwrite v778')
t=unreal.AssetImportTask();t.set_editor_properties({'filename':str(SOURCE),'destination_path':DEST,'automated':True,'replace_existing':False,'replace_existing_settings':False,'save':True})
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t]);unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
assets=lib.list_assets(DEST,recursive=True,include_folder=False);meshes=[]
for p in assets:
 a=unreal.load_asset(p)
 if isinstance(a,unreal.StaticMesh):meshes.append(p)
required=['BASE_STATIC','TURNTABLE','LOWER_ARM','UPPER_ARM','WRIST','VACUUM_TOOL'];fail=[]
if len(meshes)!=6:fail.append(f'static mesh count {len(meshes)} expected 6')
for frag in required:
 if not any(frag.lower() in p.lower() for p in meshes):fail.append('missing '+frag)
if sha()!=EXPECTED:fail.append('protected hash changed')
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps({'revision':'v778','generated_utc':datetime.now(timezone.utc).isoformat(),'status':'PASS__USER_S07_SIX_COMPONENT_INTAKE' if not fail else 'FAIL__V778','destination':DEST,'source':str(SOURCE),'static_meshes':meshes,'failures':fail,'protected_sha256':sha(),'meshy_credits_used_by_codex':0},indent=2),encoding='utf-8')
if fail:raise RuntimeError('; '.join(fail))
unreal.log('LINE_BOSS_S07_USER_ROBOT_INTAKE_V778_PASS')
