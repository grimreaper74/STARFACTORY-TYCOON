"""Duplicate retained v040 into isolated luminaire-direction candidate v041."""

import unreal


BASE = "/Game/LineBoss/Maps/LB_PressShop_PR004WrapFinishCandidate_v040"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004LuminaireCandidate_v041"
lib = unreal.EditorAssetLibrary
if not lib.does_asset_exist(MAP):
    if not lib.duplicate_asset(BASE, MAP):
        raise RuntimeError(f"Could not duplicate {BASE} to {MAP}")
    lib.save_asset(MAP, only_if_is_dirty=False)
unreal.log(f"LINE_BOSS_PR004_LUMINAIRE_V041_PREP_PASS map={MAP}")
unreal.SystemLibrary.quit_editor()
