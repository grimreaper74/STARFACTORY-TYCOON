from pathlib import Path
from datetime import datetime, timezone
import hashlib,json,unreal
ROOT=Path(unreal.Paths.project_dir());DEST='/Game/LineBoss/Developer/Validation/PressTrains/NewRigidIntake_v741'
OUT=ROOT/'Saved/Audits/PressShopIntegration/new_press_train_asset_verification_v742.json'
PROTECTED=ROOT/'Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap';EXPECTED='5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8'
def sha():return hashlib.sha256(PROTECTED.read_bytes()).hexdigest().upper()
if OUT.exists():raise RuntimeError('Refusing overwrite v742')
assets=unreal.EditorAssetLibrary.list_assets(DEST,recursive=True,include_folder=False)
meshes=[p for p in assets if isinstance(unreal.load_asset(p),unreal.StaticMesh)]
low=[p.lower() for p in meshes]
checks={
 'press_shell':any('s03_static_shell' in p for p in low),'press_ram':any('s03_ram_slide' in p for p in low),'upper_die':any('s03_upper_die' in p for p in low),'lower_die':any('s03_lower_die_bolster' in p for p in low),
 'cabinet':any('factory_elect' in p for p in low),'hmi':any('factory_opera' in p for p in low),
 'transfer_rails':any('static_rails' in p for p in low),'transfer_carriage':any('servo_carriage' in p for p in low),'transfer_z':any('crossbeam_z' in p for p in low),'gripper_left':any('gripper_left' in p for p in low),'gripper_right':any('gripper_right' in p for p in low),
 'conveyor_shell':any('roller_conveyo' in p and 'textured_static' in p for p in low),
 'rollers_15':sum(1 for p in low if '/sm_ca_rc_roller_' in p)==15,
}
fail=[k for k,v in checks.items() if not v]
if sha()!=EXPECTED:fail.append('protected_hash')
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps({'revision':'v742','generated_utc':datetime.now(timezone.utc).isoformat(),'status':'PASS__UNREAL_ASSET_INTAKE_VERIFIED' if not fail else 'FAIL__V742','source_import_audit':'new_press_train_asset_intake_v741.json','asset_count':len(assets),'static_mesh_count':len(meshes),'checks':checks,'failures':fail,'protected_sha256':sha(),'meshy_credits_used':0},indent=2),encoding='utf-8')
if fail:raise RuntimeError(';'.join(fail))
unreal.log('LINE_BOSS_NEW_PRESS_TRAIN_ASSET_VERIFY_V742_PASS')
