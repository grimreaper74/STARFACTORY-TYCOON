"""Create a clean navigation successor of functional v577."""
import unreal
SRC = "/Game/LineBoss/Developer/Validation/LB_PressShop_InboundFunctionalCandidate_v577"
DST = "/Game/LineBoss/Developer/Validation/LB_PressShop_InboundNavCandidate_v581"
lib = unreal.EditorAssetLibrary
if lib.does_asset_exist(DST): raise RuntimeError(f"Refusing overwrite {DST}")
if not lib.duplicate_asset(SRC, DST): raise RuntimeError("Could not duplicate v577")
if not lib.save_asset(DST, only_if_is_dirty=False): raise RuntimeError("Could not save v581")
unreal.log("LINE_BOSS_INBOUND_NAV_PREPARE_V581_PASS")
