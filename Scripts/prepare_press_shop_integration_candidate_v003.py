"""Create a preserved v003 derivative in an isolated Unreal editor session."""

import unreal

BASE_MAP = "/Game/LineBoss/Maps/LB_PressShop_IntegrationCandidate_v002"
DEST_MAP = "/Game/LineBoss/Maps/LB_PressShop_IntegrationCandidate_v003"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
levels.load_level("/Game/LineBoss/Maps/LB_PressShop_Foundation")
if unreal.EditorAssetLibrary.does_asset_exist(DEST_MAP):
    if not unreal.EditorAssetLibrary.delete_asset(DEST_MAP):
        raise RuntimeError(f"Could not remove previous incomplete {DEST_MAP}")
if not unreal.EditorAssetLibrary.duplicate_asset(BASE_MAP, DEST_MAP):
    raise RuntimeError(f"Could not duplicate {BASE_MAP} to {DEST_MAP}")
if not unreal.EditorAssetLibrary.save_asset(DEST_MAP, only_if_is_dirty=False):
    raise RuntimeError(f"Could not save duplicated map {DEST_MAP}")
unreal.log(f"LINE_BOSS_PRESS_SHOP_V003_PREP_PASS map={DEST_MAP}")
