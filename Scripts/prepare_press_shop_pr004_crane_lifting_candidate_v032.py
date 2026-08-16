"""Duplicate the technically gated v031 map into isolated lifting-detail candidate v032."""

import unreal


BASE = "/Game/LineBoss/Maps/LB_PressShop_PR004CraneFabricationCandidate_v031"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004CraneLiftingCandidate_v032"
library = unreal.EditorAssetLibrary

if library.does_asset_exist(MAP):
    unreal.log(f"LINE_BOSS_PR004_CRANE_V032_PREP_EXISTS map={MAP}")
else:
    if not library.duplicate_asset(BASE, MAP):
        raise RuntimeError(f"Could not duplicate {BASE} to {MAP}")
    if not library.save_asset(MAP, only_if_is_dirty=False):
        raise RuntimeError(f"Could not save {MAP}")
    unreal.log(f"LINE_BOSS_PR004_CRANE_V032_PREP_PASS map={MAP}")

unreal.SystemLibrary.quit_editor()
