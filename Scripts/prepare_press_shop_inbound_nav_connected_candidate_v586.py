import unreal
SRC="/Game/LineBoss/Developer/Validation/LB_PressShop_InboundNavCandidate_v581"
DST="/Game/LineBoss/Developer/Validation/LB_PressShop_InboundNavConnectedCandidate_v586"
lib=unreal.EditorAssetLibrary
if lib.does_asset_exist(DST):raise RuntimeError(f"Refusing overwrite {DST}")
if not lib.duplicate_asset(SRC,DST):raise RuntimeError("Could not duplicate v581")
if not lib.save_asset(DST,only_if_is_dirty=False):raise RuntimeError("Could not save v586")
