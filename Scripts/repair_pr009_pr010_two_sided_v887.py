"""Enable two-sided rendering for Meshy originals after face-winding diagnosis."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,unreal
ROOT=Path(unreal.Paths.project_dir()).resolve(); MAP='/Game/LineBoss/Maps/LB_PressShop_PR009_PR010_OriginalFBX_Isolated_v884'
PROTECTED=ROOT/r'Content\LineBoss\Maps\LB_PressShop_BuilderAuthorityCandidate_v438.umap'; EXPECTED='5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest().upper(); before=sha(PROTECTED)
if before!=EXPECTED:raise RuntimeError('protected invariant')
lib=unreal.EditorAssetLibrary; records=[]
for station in ('PR009','PR010'):
 path=f'/Game/LineBoss/Candidates/PressShop/PR009_PR010_OriginalFBX_v884/{station}/Materials/M_{station}_OriginalPBR_v884'
 mat=lib.load_asset(path)
 if not isinstance(mat,unreal.Material):raise RuntimeError(path)
 mat.set_editor_property('two_sided',True);unreal.MaterialEditingLibrary.recompile_material(mat);lib.save_loaded_asset(mat,False);records.append({'station':station,'material':path,'two_sided':mat.get_editor_property('two_sided')})
after=sha(PROTECTED)
if after!=before:raise RuntimeError('protected changed')
out=ROOT/r'Saved\Audits\PressShopIntegration\pr009_pr010_two_sided_repair_v887.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps({'generated_utc':datetime.now(timezone.utc).isoformat(),'status':'TWO_SIDED_DIAGNOSTIC_APPLIED__VISUAL_REVIEW_REQUIRED','map':MAP,'records':records,'protected_v438_before':before,'protected_v438_after':after},indent=2),encoding='utf-8');unreal.log('LINE_BOSS_PR009_PR010_TWO_SIDED_V887_PASS')
