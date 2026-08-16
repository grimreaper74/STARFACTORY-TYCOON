"""Duplicate rejected v007 into a fresh v008 package, save it, then exit."""

import unreal


SOURCE_MAP = "/Game/LineBoss/Developer/Validation/PR004/LB_PR004_Depackaging_Candidate_v007"
MAP = "/Game/LineBoss/Developer/Validation/PR004/LB_PR004_Inspection_Candidate_v008"

try:
    if unreal.EditorAssetLibrary.does_asset_exist(MAP):
        if not unreal.EditorAssetLibrary.delete_asset(MAP):
            raise RuntimeError(f"Could not remove prior {MAP}")

    duplicated = unreal.EditorAssetLibrary.duplicate_asset(SOURCE_MAP, MAP)
    if not duplicated:
        raise RuntimeError(f"Could not duplicate {SOURCE_MAP} to {MAP}")
    if not unreal.EditorAssetLibrary.save_asset(MAP, only_if_is_dirty=False):
        raise RuntimeError(f"Could not save duplicated map {MAP}")
    if not unreal.EditorAssetLibrary.does_asset_exist(MAP):
        raise RuntimeError(f"Duplicated map did not remain registered: {MAP}")

    unreal.log(f"LINE_BOSS_PR004_PREPARE_V008_PASS map={MAP}")
except Exception as exc:
    unreal.log_error(f"LINE_BOSS_PR004_PREPARE_V008_FAIL error={exc}")
    raise
finally:
    unreal.SystemLibrary.quit_editor()
