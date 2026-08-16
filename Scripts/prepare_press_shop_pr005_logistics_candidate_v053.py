"""Duplicate unpromoted v052 into isolated PR-005 logistics v053."""

import unreal

BASE = "/Game/LineBoss/Maps/LB_PressShop_PR005ServiceIdentityCandidate_v052"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR005LogisticsCandidate_v053"
library = unreal.EditorAssetLibrary
if not library.does_asset_exist(MAP):
    if not library.duplicate_asset(BASE, MAP):
        raise RuntimeError(f"Could not duplicate {BASE} to {MAP}")
    library.save_asset(MAP, only_if_is_dirty=False)
unreal.log(f"LINE_BOSS_PR005_LOGISTICS_V053_DUPLICATE_PASS base={BASE} map={MAP}")
unreal.SystemLibrary.quit_editor()

