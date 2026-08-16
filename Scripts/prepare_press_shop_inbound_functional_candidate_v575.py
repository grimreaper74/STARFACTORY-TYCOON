"""Create an immutable successor of retained visual candidate v570."""
from pathlib import Path
import unreal

SRC = "/Game/LineBoss/Developer/Validation/LB_PressShop_InboundIntegrationCandidate_v570"
DST = "/Game/LineBoss/Developer/Validation/LB_PressShop_InboundFunctionalCandidate_v575"
library = unreal.EditorAssetLibrary
if library.does_asset_exist(DST):
    raise RuntimeError(f"Refusing overwrite {DST}")
if not library.duplicate_asset(SRC, DST):
    raise RuntimeError("Could not duplicate retained v570")
if not library.save_asset(DST, only_if_is_dirty=False):
    raise RuntimeError("Could not save v575")
unreal.log("LINE_BOSS_INBOUND_FUNCTIONAL_PREPARE_V575_PASS")
