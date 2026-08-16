"""Duplicate v042 into an isolated PR-005 live-HMI candidate, then exit."""

import unreal


BASE = "/Game/LineBoss/Maps/LB_PressShop_PR004PR005HandoffCandidate_v042"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR005LiveHMICandidate_v043"
library = unreal.EditorAssetLibrary
if not library.does_asset_exist(MAP):
    if not library.duplicate_asset(BASE, MAP):
        raise RuntimeError(f"Could not duplicate {BASE} to {MAP}")
    library.save_asset(MAP, only_if_is_dirty=False)
unreal.log(f"LINE_BOSS_PR005_LIVE_HMI_V043_DUPLICATE_PASS map={MAP}")
unreal.SystemLibrary.quit_editor()
