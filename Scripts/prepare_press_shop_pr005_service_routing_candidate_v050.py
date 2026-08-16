"""Duplicate unpromoted v049 into isolated PR-005 service-routing v050."""

import unreal


BASE = "/Game/LineBoss/Maps/LB_PressShop_PR005FloorJunctionCandidate_v049"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR005ServiceRoutingCandidate_v050"
library = unreal.EditorAssetLibrary
if not library.does_asset_exist(MAP):
    if not library.duplicate_asset(BASE, MAP):
        raise RuntimeError(f"Could not duplicate {BASE} to {MAP}")
    library.save_asset(MAP, only_if_is_dirty=False)
unreal.log(f"LINE_BOSS_PR005_SERVICE_ROUTING_V050_DUPLICATE_PASS base={BASE} map={MAP}")
unreal.SystemLibrary.quit_editor()
