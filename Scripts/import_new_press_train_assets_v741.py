from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, unreal

ROOT=Path(unreal.Paths.project_dir())
DEST='/Game/LineBoss/Developer/Validation/PressTrains/NewRigidIntake_v741'
AUDIT=ROOT/'Saved/Audits/PressShopIntegration/new_press_train_asset_intake_v741.json'
PROTECTED=ROOT/'Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap'
EXPECTED='5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8'
SOURCES=[
 Path(r'C:\Users\greg_\Projects\LineBoss_Workspace\SourceAssets\Candidate\PressTrains\TrainA\S03_v632ControlsAssembly_v735\Cairnwell_S03_Movable_v632Controls_v735.glb'),
 Path(r'C:\Users\greg_\Projects\LineBoss_Workspace\SourceAssets\Candidate\PressTrains\Shared\InterPressTransferRigid_v737\CA_InterPressTransferRigid_v737.glb'),
 Path(r'C:\Users\greg_\Projects\LineBoss_Workspace\SourceAssets\Candidate\PressTrains\Shared\UserRollerConveyorSalvage_v740\Cairnwell_RollerConveyor_Movable_v740.glb'),
]
def sha():return hashlib.sha256(PROTECTED.read_bytes()).hexdigest().upper()
lib=unreal.EditorAssetLibrary
if sha()!=EXPECTED:raise RuntimeError('Protected v438 hash mismatch before import')
if AUDIT.exists():raise RuntimeError('Refusing overwrite v741 audit')
if lib.does_directory_exist(DEST):
    existing=lib.list_assets(DEST,recursive=True,include_folder=False)
    if existing:raise RuntimeError(f'Refusing non-empty destination {DEST}: {len(existing)} assets')
for p in SOURCES:
    if not p.is_file():raise RuntimeError(f'Missing source {p}')
tasks=[]
for p in SOURCES:
    t=unreal.AssetImportTask();t.set_editor_properties({'filename':str(p),'destination_path':DEST,'automated':True,'replace_existing':False,'replace_existing_settings':False,'save':True})
    tasks.append(t)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
assets=lib.list_assets(DEST,recursive=True,include_folder=False)
rows=[]
for path in assets:
    a=unreal.load_asset(path)
    rows.append({'path':path,'class':a.get_class().get_name() if a else None})
fail=[]
for required in ['S03_STATIC_SHELL','S03_RAM_SLIDE','S03_UPPER_DIE','S03_LOWER_DIE_BOLSTER','STATIC_RAILS','SERVO_CARRIAGE','CROSSBEAM_Z','GRIPPER_LEFT','GRIPPER_RIGHT','ROLLER_CONVEYOR_TEXTURED_STATIC']:
    if not any(required.lower() in r['path'].lower() for r in rows):fail.append('missing '+required)
if sha()!=EXPECTED:fail.append('protected v438 changed')
AUDIT.parent.mkdir(parents=True,exist_ok=True)
AUDIT.write_text(json.dumps({'revision':'v741','generated_utc':datetime.now(timezone.utc).isoformat(),'status':'PASS__NEW_PRESS_TRAIN_ASSET_INTAKE' if not fail else 'FAIL__V741','destination':DEST,'sources':[str(p) for p in SOURCES],'asset_count':len(rows),'assets':rows,'failures':fail,'protected_sha256':sha(),'meshy_credits_used':0},indent=2),encoding='utf-8')
if fail:raise RuntimeError('; '.join(fail))
unreal.log('LINE_BOSS_NEW_PRESS_TRAIN_ASSET_INTAKE_V741_PASS')
