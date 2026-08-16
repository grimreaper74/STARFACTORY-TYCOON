from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, unreal

ROOT=Path(unreal.Paths.project_dir())
DEST='/Game/LineBoss/Developer/Validation/PressTrains/SegmentedTransferRuntime_v747'
OUT=ROOT/'Saved/Audits/PressShopIntegration/segmented_transfer_runtime_verification_v747b.json'
PROTECTED=ROOT/'Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap'
EXPECTED='5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8'
sha=lambda:hashlib.sha256(PROTECTED.read_bytes()).hexdigest().upper()
assets=unreal.EditorAssetLibrary.list_assets(DEST,recursive=True,include_folder=False)
meshes=[]
for p in assets:
    a=unreal.load_asset(p)
    if isinstance(a,unreal.StaticMesh):meshes.append(p)
need=['TIC_FRAME','CROSSBEAM','ATOR_PACK','CUP_ARRAY']
fail=[f'missing imported component fragment {n}' for n in need if not any(n.lower() in p.lower() for p in meshes)]
if len(meshes)!=4:fail.append(f'static mesh count {len(meshes)} expected 4')
if sha()!=EXPECTED:fail.append('protected v438 changed')
if OUT.exists():raise RuntimeError('Refusing overwrite v747b audit')
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps({'revision':'v747b','generated_utc':datetime.now(timezone.utc).isoformat(),'status':'PASS__FOUR_SEGMENTED_TRANSFER_COMPONENTS' if not fail else 'FAIL__V747B','static_meshes':meshes,'failures':fail,'protected_sha256':sha(),'meshy_credits_used':0},indent=2),encoding='utf-8')
if fail:raise RuntimeError('; '.join(fail))
unreal.log('LINE_BOSS_SEGMENTED_TRANSFER_RUNTIME_V747B_PASS')
