"""Preserve v003 and create a separate mothballed-state v004 candidate."""

import unreal

BASE_MAP = "/Game/LineBoss/Maps/LB_PressShop_IntegrationCandidate_v003"
DEST_MAP = "/Game/LineBoss/Maps/LB_PressShop_MothballedCandidate_v004"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
levels.load_level("/Game/LineBoss/Maps/LB_PressShop_Foundation")
if unreal.EditorAssetLibrary.does_asset_exist(DEST_MAP):
    raise RuntimeError(f"Preserving existing candidate; refusing to overwrite {DEST_MAP}")
if not unreal.EditorAssetLibrary.duplicate_asset(BASE_MAP, DEST_MAP):
    raise RuntimeError(f"Could not duplicate {BASE_MAP} to {DEST_MAP}")
if not unreal.EditorAssetLibrary.save_asset(DEST_MAP, only_if_is_dirty=False):
    raise RuntimeError(f"Could not save {DEST_MAP}")
unreal.log(f"LINE_BOSS_PRESS_SHOP_V004_PREP_PASS map={DEST_MAP}")

