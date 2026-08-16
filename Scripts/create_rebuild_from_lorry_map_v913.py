from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import unreal

SOURCE = '/Game/LineBoss/Maps/LB_PressShop_CleanShell_v20260809_v003'
DEST = '/Game/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913'
ROOT = Path(unreal.Paths.project_dir()).resolve()
SOURCE_FILE = ROOT / 'Content/LineBoss/Maps/LB_PressShop_CleanShell_v20260809_v003.umap'
PROTECTED_FILE = ROOT / 'Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap'
SOURCE_HASH = '38B38A5FB1322B6D4B7D3751FB921FC1F442EA65B9196D647A10BB6EC9262485'
PROTECTED_HASH = '5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()

if sha(SOURCE_FILE) != SOURCE_HASH:
    raise RuntimeError('Clean-shell source hash mismatch')
if sha(PROTECTED_FILE) != PROTECTED_HASH:
    raise RuntimeError('Protected v438 hash mismatch')
if unreal.EditorAssetLibrary.does_asset_exist(DEST):
    raise RuntimeError('Destination map already exists')
if not unreal.EditorAssetLibrary.duplicate_asset(SOURCE, DEST):
    raise RuntimeError('Map duplication failed')
unreal.EditorAssetLibrary.save_asset(DEST, only_if_is_dirty=False)

dest_file = ROOT / 'Content/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913.umap'
if not dest_file.exists():
    raise RuntimeError('Destination map file was not written')
if sha(SOURCE_FILE) != SOURCE_HASH or sha(PROTECTED_FILE) != PROTECTED_HASH:
    raise RuntimeError('Authority source changed during duplication')

audit = ROOT / 'Saved/Audits/PressShopIntegration/rebuild_from_lorry_map_creation_v20260810_v913.json'
audit.parent.mkdir(parents=True, exist_ok=True)
audit.write_text(json.dumps({
    'generated_utc': datetime.now(timezone.utc).isoformat(),
    'status': 'PASS__FRESH_CLEAN_SHELL_CHILD__ZERO_PRODUCTION_ACTORS_AT_SOURCE',
    'source': SOURCE,
    'map': DEST,
    'source_hash': SOURCE_HASH,
    'destination_hash': sha(dest_file),
    'protected_v438_hash': PROTECTED_HASH,
    'build_order': 'loaded lorry first; work downstream to wider Press Trains A-D',
    'meshy_credits_used': 0
}, indent=2), encoding='utf-8')
unreal.log('LINE_BOSS_REBUILD_FROM_LORRY_MAP_V913_PASS')
