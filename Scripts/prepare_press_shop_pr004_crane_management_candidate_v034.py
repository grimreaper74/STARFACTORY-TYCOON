"""Duplicate the gated v033 crane map into isolated management candidate v034."""

import unreal


BASE = "/Game/LineBoss/Maps/LB_PressShop_PR004CraneCHookCandidate_v033"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004CraneManagementCandidate_v034"
library = unreal.EditorAssetLibrary
if not library.does_asset_exist(MAP):
    if not library.duplicate_asset(BASE, MAP):
        raise RuntimeError(f"Could not duplicate {BASE} to {MAP}")
    library.save_asset(MAP, only_if_is_dirty=False)
unreal.log(f"LINE_BOSS_PR004_CRANE_V034_PREP_PASS map={MAP}")
unreal.SystemLibrary.quit_editor()
