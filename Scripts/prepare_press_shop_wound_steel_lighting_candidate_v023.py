"""Prepare the preserved v023 map package without loading it in this process."""

import unreal


SOURCE = "/Game/LineBoss/Maps/LB_PressShop_WoundSteelFrontEndCandidate_v022"
DEST = "/Game/LineBoss/Maps/LB_PressShop_WoundSteelLightingCandidate_v023"
lib = unreal.EditorAssetLibrary

if lib.does_asset_exist(DEST):
    raise RuntimeError(f"Refusing to overwrite preserved candidate {DEST}")
if not lib.duplicate_asset(SOURCE, DEST):
    raise RuntimeError("Could not duplicate preserved v022 map")
if not lib.save_asset(DEST, only_if_is_dirty=False):
    raise RuntimeError("Could not save prepared v023 map")

unreal.log(f"LINE_BOSS_WOUND_STEEL_LIGHTING_V023_PREPARE_PASS map={DEST}")
unreal.SystemLibrary.quit_editor()
