"""Duplicate preserved PR-005 v045 into isolated CAD floor candidate v048."""

import unreal


BASE = "/Game/LineBoss/Maps/LB_PressShop_PR005CoilFinishCandidate_v045"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR005CADFloorCandidate_v048"
library = unreal.EditorAssetLibrary
if not library.does_asset_exist(MAP):
    if not library.duplicate_asset(BASE, MAP):
        raise RuntimeError(f"Could not duplicate {BASE} to {MAP}")
    library.save_asset(MAP, only_if_is_dirty=False)
unreal.log(f"LINE_BOSS_PR005_CAD_FLOOR_V048_DUPLICATE_PASS base={BASE} map={MAP}")
unreal.SystemLibrary.quit_editor()
