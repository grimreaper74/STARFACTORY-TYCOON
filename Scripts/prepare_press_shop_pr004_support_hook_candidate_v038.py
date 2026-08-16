"""Duplicate v037 into isolated support-hook finish candidate v038."""

import unreal

BASE = "/Game/LineBoss/Maps/LB_PressShop_PR004SupportHookCandidate_v037"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004SupportHookCandidate_v038"
library = unreal.EditorAssetLibrary
if not library.does_asset_exist(MAP):
    if not library.duplicate_asset(BASE, MAP):
        raise RuntimeError(f"Could not duplicate {BASE} to {MAP}")
    library.save_asset(MAP, only_if_is_dirty=False)
unreal.log(f"LINE_BOSS_PR004_SUPPORT_HOOK_V038_PREP_PASS map={MAP}")
unreal.SystemLibrary.quit_editor()
