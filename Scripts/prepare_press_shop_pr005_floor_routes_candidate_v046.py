"""Duplicate unpromoted v045 into isolated PR-005 floor-route candidate v046."""

import unreal


BASE = "/Game/LineBoss/Maps/LB_PressShop_PR005CoilFinishCandidate_v045"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR005FloorRoutesCandidate_v046"
library = unreal.EditorAssetLibrary
if not library.does_asset_exist(MAP):
    if not library.duplicate_asset(BASE, MAP):
        raise RuntimeError(f"Could not duplicate {BASE} to {MAP}")
    library.save_asset(MAP, only_if_is_dirty=False)
unreal.log(f"LINE_BOSS_PR005_FLOOR_ROUTES_V046_DUPLICATE_PASS map={MAP}")
unreal.SystemLibrary.quit_editor()
