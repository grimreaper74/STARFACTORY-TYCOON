"""Prepare the preserved v022 map package without loading it in this process."""

import unreal


SOURCE = "/Game/LineBoss/Maps/LB_PressShop_BareCoilFrontEndCandidate_v021"
DEST = "/Game/LineBoss/Maps/LB_PressShop_WoundSteelFrontEndCandidate_v022"
lib = unreal.EditorAssetLibrary
if lib.does_asset_exist(DEST):
    raise RuntimeError(f"Refusing to overwrite preserved candidate {DEST}")
if not lib.duplicate_asset(SOURCE, DEST):
    raise RuntimeError("Could not duplicate preserved v021 map")
if not lib.save_asset(DEST, only_if_is_dirty=False):
    raise RuntimeError("Could not save prepared v022 map")
unreal.log(f"LINE_BOSS_WOUND_STEEL_V022_PREPARE_PASS map={DEST}")
unreal.SystemLibrary.quit_editor()
