"""Duplicate repaired v008 into a fresh map-fit v009 package and save it."""

import unreal


SOURCE = "/Game/LineBoss/Developer/Validation/PR004/LB_PR004_Inspection_Candidate_v008"
DEST = "/Game/LineBoss/Developer/Validation/PR004/LB_PR004_Inspection_Candidate_v009"

try:
    if unreal.EditorAssetLibrary.does_asset_exist(DEST):
        if not unreal.EditorAssetLibrary.delete_asset(DEST):
            raise RuntimeError(f"Could not remove prior {DEST}")
    duplicated = unreal.EditorAssetLibrary.duplicate_asset(SOURCE, DEST)
    if not duplicated or not unreal.EditorAssetLibrary.save_asset(DEST, only_if_is_dirty=False):
        raise RuntimeError(f"Could not duplicate/save {DEST}")
    if not unreal.EditorAssetLibrary.does_asset_exist(DEST):
        raise RuntimeError(f"Destination did not remain registered: {DEST}")
    unreal.log(f"LINE_BOSS_PR004_PREPARE_V009_PASS map={DEST}")
finally:
    unreal.SystemLibrary.quit_editor()
