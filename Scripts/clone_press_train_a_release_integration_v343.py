"""Phase 1: clone retained v301 to a fresh v343 package, then exit before loading it."""
import unreal

SOURCE = "/Game/LineBoss/Maps/LB_PressShop_TrainAWideSpanClearanceCandidate_v301"
TARGET = "/Game/LineBoss/Maps/LB_PressShop_TrainAReleaseIntegrationCandidate_v343"
lib = unreal.EditorAssetLibrary
if lib.does_asset_exist(TARGET):
    raise RuntimeError("Refusing to overwrite v343")
if not lib.duplicate_asset(SOURCE, TARGET):
    raise RuntimeError("Could not clone v301 to v343")
if not lib.save_asset(TARGET, only_if_is_dirty=False):
    raise RuntimeError("Could not persist v343 clone")
unreal.log("LB_TRAIN_A_V343_CLONE_PASS")
unreal.SystemLibrary.quit_editor()
