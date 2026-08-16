"""Duplicate unpromoted v039 into isolated package-surface candidate v040."""

import unreal


BASE = "/Game/LineBoss/Maps/LB_PressShop_PR004TraceabilityCandidate_v039"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004WrapFinishCandidate_v040"
library = unreal.EditorAssetLibrary
if not library.does_asset_exist(MAP):
    if not library.duplicate_asset(BASE, MAP):
        raise RuntimeError(f"Could not duplicate {BASE} to {MAP}")
    library.save_asset(MAP, only_if_is_dirty=False)
unreal.log(f"LINE_BOSS_PR004_WRAP_FINISH_V040_PREP_PASS map={MAP}")
unreal.SystemLibrary.quit_editor()
