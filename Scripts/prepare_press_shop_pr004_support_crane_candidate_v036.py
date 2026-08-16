"""Duplicate the retained v035 direction checkpoint into isolated v036."""

import unreal


BASE = "/Game/LineBoss/Maps/LB_PressShop_PR004CraneFinishCandidate_v035"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004SupportCraneCandidate_v036"
library = unreal.EditorAssetLibrary
if not library.does_asset_exist(MAP):
    if not library.duplicate_asset(BASE, MAP):
        raise RuntimeError(f"Could not duplicate {BASE} to {MAP}")
    library.save_asset(MAP, only_if_is_dirty=False)
unreal.log(f"LINE_BOSS_PR004_SUPPORT_CRANE_V036_PREP_PASS map={MAP}")
unreal.SystemLibrary.quit_editor()
