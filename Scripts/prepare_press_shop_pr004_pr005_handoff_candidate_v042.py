"""Duplicate unpromoted v041 into isolated PR-004/PR-005 handoff candidate v042."""

import unreal

BASE = "/Game/LineBoss/Maps/LB_PressShop_PR004LuminaireCandidate_v041"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004PR005HandoffCandidate_v042"
library = unreal.EditorAssetLibrary
if not library.does_asset_exist(MAP):
    if not library.duplicate_asset(BASE, MAP):
        raise RuntimeError(f"Could not duplicate {BASE} to {MAP}")
    library.save_asset(MAP, only_if_is_dirty=False)
unreal.log(f"LINE_BOSS_PR004_PR005_HANDOFF_V042_PREP_PASS map={MAP}")
unreal.SystemLibrary.quit_editor()
