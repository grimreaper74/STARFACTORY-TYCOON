from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,unreal
ROOT=Path(unreal.Paths.project_dir()).resolve();PROTECTED=ROOT/r'Content\LineBoss\Maps\LB_PressShop_BuilderAuthorityCandidate_v438.umap';EXPECTED='5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest().upper();before=sha(PROTECTED)
if before!=EXPECTED:raise RuntimeError('protected invariant')
lib=unreal.EditorAssetLibrary;records=[]
for station in ('PR009','PR010'):
 path=f'/Game/LineBoss/Candidates/PressShop/PR009_PR010_OriginalFBX_v884/{station}/SM_CA_MW_{station}_OriginalHighPoly_v883';mesh=lib.load_asset(path)
 if not isinstance(mesh,unreal.StaticMesh):raise RuntimeError(path)
 ns=mesh.get_editor_property('nanite_settings');ns.enabled=False;mesh.set_editor_property('nanite_settings',ns);lib.save_loaded_asset(mesh,False);records.append({'station':station,'mesh':path,'nanite_enabled':mesh.get_editor_property('nanite_settings').enabled})
after=sha(PROTECTED)
if after!=before:raise RuntimeError('protected changed')
out=ROOT/r'Saved\Audits\PressShopIntegration\pr009_pr010_nanite_disabled_v889.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps({'generated_utc':datetime.now(timezone.utc).isoformat(),'status':'NANITE_DISABLED__VISUAL_REVIEW_REQUIRED','records':records,'protected_v438_before':before,'protected_v438_after':after},indent=2),encoding='utf-8');unreal.log('LINE_BOSS_PR009_PR010_NANITE_DISABLED_V889_PASS')
