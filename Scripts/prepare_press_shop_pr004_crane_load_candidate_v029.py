"""Duplicate v028 into an isolated v029 crane-load visual candidate."""

import unreal


BASE = "/Game/LineBoss/Maps/LB_PressShop_PR004CraneVisualCandidate_v028"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004CraneLoadCandidate_v029"
library = unreal.EditorAssetLibrary

if library.does_asset_exist(MAP):
    unreal.log(f"LINE_BOSS_PR004_CRANE_V029_PREP_EXISTS map={MAP}")
else:
    if not library.duplicate_asset(BASE, MAP):
        raise RuntimeError(f"Could not duplicate {BASE} to {MAP}")
    if not library.save_asset(MAP, only_if_is_dirty=False):
        raise RuntimeError(f"Could not save duplicated map {MAP}")
    unreal.log(f"LINE_BOSS_PR004_CRANE_V029_PREP_PASS map={MAP}")

unreal.SystemLibrary.quit_editor()
