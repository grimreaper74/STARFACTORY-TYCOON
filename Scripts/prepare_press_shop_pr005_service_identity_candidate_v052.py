"""Duplicate unpromoted v051 into isolated PR-005 service-identity v052."""

import unreal


BASE = "/Game/LineBoss/Maps/LB_PressShop_PR005ServiceCoversCandidate_v051"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR005ServiceIdentityCandidate_v052"
library = unreal.EditorAssetLibrary
if not library.does_asset_exist(MAP):
    if not library.duplicate_asset(BASE, MAP):
        raise RuntimeError(f"Could not duplicate {BASE} to {MAP}")
    library.save_asset(MAP, only_if_is_dirty=False)
unreal.log(f"LINE_BOSS_PR005_SERVICE_IDENTITY_V052_DUPLICATE_PASS base={BASE} map={MAP}")
unreal.SystemLibrary.quit_editor()
