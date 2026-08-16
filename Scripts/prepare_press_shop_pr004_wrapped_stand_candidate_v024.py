"""Prepare isolated v024 from the preserved v023 visual stepping stone."""

import unreal


SOURCE = "/Game/LineBoss/Maps/LB_PressShop_WoundSteelLightingCandidate_v023"
DEST = "/Game/LineBoss/Maps/LB_PressShop_PR004WrappedStandCandidate_v024"
lib = unreal.EditorAssetLibrary

if lib.does_asset_exist(DEST):
    raise RuntimeError(f"Refusing to overwrite preserved candidate {DEST}")
if not lib.duplicate_asset(SOURCE, DEST):
    raise RuntimeError("Could not duplicate preserved v023 map")
if not lib.save_asset(DEST, only_if_is_dirty=False):
    raise RuntimeError("Could not save prepared v024 map")

unreal.log(f"LINE_BOSS_PR004_WRAPPED_STAND_V024_PREPARE_PASS map={DEST}")
unreal.SystemLibrary.quit_editor()
