"""Duplicate unpromoted v043 into isolated PR-005 material candidate v044."""

import unreal


BASE = "/Game/LineBoss/Maps/LB_PressShop_PR005LiveHMICandidate_v043"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR005MaterialCandidate_v044"
library = unreal.EditorAssetLibrary
if not library.does_asset_exist(MAP):
    if not library.duplicate_asset(BASE, MAP):
        raise RuntimeError(f"Could not duplicate {BASE} to {MAP}")
    library.save_asset(MAP, only_if_is_dirty=False)
unreal.log(f"LINE_BOSS_PR005_MATERIAL_V044_DUPLICATE_PASS map={MAP}")
unreal.SystemLibrary.quit_editor()
