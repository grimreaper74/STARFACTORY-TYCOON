"""Duplicate unpromoted v050 into isolated PR-005 service-cover v051."""

import unreal


BASE = "/Game/LineBoss/Maps/LB_PressShop_PR005ServiceRoutingCandidate_v050"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR005ServiceCoversCandidate_v051"
library = unreal.EditorAssetLibrary
if not library.does_asset_exist(MAP):
    if not library.duplicate_asset(BASE, MAP):
        raise RuntimeError(f"Could not duplicate {BASE} to {MAP}")
    library.save_asset(MAP, only_if_is_dirty=False)
unreal.log(f"LINE_BOSS_PR005_SERVICE_COVERS_V051_DUPLICATE_PASS base={BASE} map={MAP}")
unreal.SystemLibrary.quit_editor()
