"""Duplicate the technically passed v029 map into isolated visual v030."""

import unreal


BASE = "/Game/LineBoss/Maps/LB_PressShop_PR004CraneLoadCandidate_v029"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004CraneVisualCandidate_v030"
library = unreal.EditorAssetLibrary

if library.does_asset_exist(MAP):
    unreal.log(f"LINE_BOSS_PR004_CRANE_V030_PREP_EXISTS map={MAP}")
else:
    if not library.duplicate_asset(BASE, MAP):
        raise RuntimeError(f"Could not duplicate {BASE} to {MAP}")
    if not library.save_asset(MAP, only_if_is_dirty=False):
        raise RuntimeError(f"Could not save duplicated map {MAP}")
    unreal.log(f"LINE_BOSS_PR004_CRANE_V030_PREP_PASS map={MAP}")

unreal.SystemLibrary.quit_editor()
