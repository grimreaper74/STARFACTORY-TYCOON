"""Duplicate retained v038 into isolated live-traceability candidate v039."""

import unreal


BASE = "/Game/LineBoss/Maps/LB_PressShop_PR004SupportHookCandidate_v038"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004TraceabilityCandidate_v039"
library = unreal.EditorAssetLibrary

if not library.does_asset_exist(MAP):
    if not library.duplicate_asset(BASE, MAP):
        raise RuntimeError(f"Could not duplicate {BASE} to {MAP}")
    library.save_asset(MAP, only_if_is_dirty=False)

unreal.log(f"LINE_BOSS_PR004_TRACEABILITY_V039_PREP_PASS map={MAP}")
unreal.SystemLibrary.quit_editor()
