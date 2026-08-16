"""Duplicate unpromoted v046 into isolated dimensioned-route candidate v047."""

import unreal


BASE = "/Game/LineBoss/Maps/LB_PressShop_PR005FloorRoutesCandidate_v046"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR005DimensionedRoutesCandidate_v047"
library = unreal.EditorAssetLibrary
if not library.does_asset_exist(MAP):
    if not library.duplicate_asset(BASE, MAP):
        raise RuntimeError(f"Could not duplicate {BASE} to {MAP}")
    library.save_asset(MAP, only_if_is_dirty=False)
unreal.log(f"LINE_BOSS_PR005_DIMENSIONED_ROUTES_V047_DUPLICATE_PASS map={MAP}")
unreal.SystemLibrary.quit_editor()
