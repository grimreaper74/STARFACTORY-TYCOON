"""Duplicate the runtime-proved v027 map to an isolated v028 visual candidate."""

import unreal


BASE = "/Game/LineBoss/Maps/LB_PressShop_PR004CraneRuntimeCandidate_v027"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004CraneVisualCandidate_v028"
library = unreal.EditorAssetLibrary

if library.does_asset_exist(MAP):
    unreal.log(f"LINE_BOSS_PR004_CRANE_V028_PREP_EXISTS map={MAP}")
else:
    if not library.duplicate_asset(BASE, MAP):
        raise RuntimeError(f"Could not duplicate {BASE} to {MAP}")
    if not library.save_asset(MAP, only_if_is_dirty=False):
        raise RuntimeError(f"Could not save duplicated map {MAP}")
    unreal.log(f"LINE_BOSS_PR004_CRANE_V028_PREP_PASS map={MAP}")
