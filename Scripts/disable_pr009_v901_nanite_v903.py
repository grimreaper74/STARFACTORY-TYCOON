from pathlib import Path
import hashlib,unreal
R=Path(unreal.Paths.project_dir()).resolve();P=R/r'Content\LineBoss\Maps\LB_PressShop_BuilderAuthorityCandidate_v438.umap';E='5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest().upper();b=sha(P)
if b!=E:raise RuntimeError('protected invariant')
lib=unreal.EditorAssetLibrary;m=lib.load_asset('/Game/LineBoss/Candidates/PressShop/PR009_OriginalFBX_v901/SM_CA_MW_PR009_OriginalHighPoly_v883');n=m.get_editor_property('nanite_settings');n.enabled=False;m.set_editor_property('nanite_settings',n);lib.save_asset(m.get_path_name(),False)
if sha(P)!=b:raise RuntimeError('protected changed')
unreal.log('LINE_BOSS_PR009_V901_NANITE_DISABLED_V903_PASS')
