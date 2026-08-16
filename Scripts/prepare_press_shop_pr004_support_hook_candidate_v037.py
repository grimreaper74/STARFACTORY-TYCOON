"""Duplicate the technically gated v036 map into isolated visual candidate v037."""

import unreal

BASE = "/Game/LineBoss/Maps/LB_PressShop_PR004SupportCraneCandidate_v036"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004SupportHookCandidate_v037"
library = unreal.EditorAssetLibrary
if not library.does_asset_exist(MAP):
    if not library.duplicate_asset(BASE, MAP):
        raise RuntimeError(f"Could not duplicate {BASE} to {MAP}")
    library.save_asset(MAP, only_if_is_dirty=False)
unreal.log(f"LINE_BOSS_PR004_SUPPORT_HOOK_V037_PREP_PASS map={MAP}")
unreal.SystemLibrary.quit_editor()
