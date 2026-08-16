from pathlib import Path
import hashlib,unreal
ROOT=Path(unreal.Paths.project_dir()).resolve();P=ROOT/r'Content\LineBoss\Maps\LB_PressShop_BuilderAuthorityCandidate_v438.umap';E='5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest().upper();b=sha(P)
if b!=E:raise RuntimeError('protected invariant')
lib=unreal.EditorAssetLibrary
for s in ('PR009','PR010'):
 m=lib.load_asset(f'/Game/LineBoss/Candidates/PressShop/PR009_PR010_OriginalFBX_v884/{s}/SM_CA_MW_{s}_OriginalHighPoly_v883');n=m.get_editor_property('nanite_settings');n.enabled=True;m.set_editor_property('nanite_settings',n);lib.save_loaded_asset(m,False)
if sha(P)!=b:raise RuntimeError('protected changed')
unreal.log('LINE_BOSS_PR009_PR010_NANITE_ENABLED_V898_PASS')
