"""Prepare a fresh visual successor from the fully tested inbound v586 map."""
import unreal

SRC = "/Game/LineBoss/Developer/Validation/LB_PressShop_InboundNavConnectedCandidate_v586"
DST = "/Game/LineBoss/Developer/Validation/LB_PressShop_InboundReleaseCandidate_v596"
library = unreal.EditorAssetLibrary

if not library.does_asset_exist(SRC):
    raise RuntimeError(f"Missing retained technical candidate: {SRC}")
if library.does_asset_exist(DST):
    raise RuntimeError(f"Refusing to overwrite existing candidate: {DST}")
if not library.duplicate_asset(SRC, DST):
    raise RuntimeError(f"Could not duplicate {SRC} to {DST}")
if not library.save_asset(DST, only_if_is_dirty=False):
    raise RuntimeError(f"Could not save {DST}")

unreal.log("LINE_BOSS_INBOUND_RELEASE_PREPARE_V596_PASS")
