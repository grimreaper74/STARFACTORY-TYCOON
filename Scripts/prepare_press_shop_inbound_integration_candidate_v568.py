"""Prepare the direct-v438 child in a separate process to avoid UE world GC leaks."""
from pathlib import Path
import hashlib
import unreal

ROOT = Path(unreal.Paths.project_dir())
SRC = "/Game/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438"
MAP = "/Game/LineBoss/Developer/Validation/LB_PressShop_InboundIntegrationCandidate_v568"
SRC_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap"
EXPECTED = "5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8"
library = unreal.EditorAssetLibrary

before = hashlib.sha256(SRC_FILE.read_bytes()).hexdigest().upper()
if before != EXPECTED:
    raise RuntimeError(f"Protected v438 hash mismatch: {before}")
if library.does_asset_exist(MAP):
    raise RuntimeError(f"Refusing overwrite {MAP}")
if not library.duplicate_asset(SRC, MAP):
    raise RuntimeError("Could not duplicate protected v438")
if not library.save_asset(MAP, only_if_is_dirty=False):
    raise RuntimeError("Could not save prepared v568")
after = hashlib.sha256(SRC_FILE.read_bytes()).hexdigest().upper()
if after != before:
    raise RuntimeError("Protected v438 changed while preparing child")
unreal.log("LINE_BOSS_INBOUND_DIRECT_V438_PREPARE_V568_PASS")
