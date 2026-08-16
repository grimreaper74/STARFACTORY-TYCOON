"""Prepare isolated v025 from the preserved interactive v024 checkpoint."""

import unreal


SOURCE = "/Game/LineBoss/Maps/LB_PressShop_PR004WrappedStandCandidate_v024"
DEST = "/Game/LineBoss/Maps/LB_PressShop_PR004InteractiveFloorCandidate_v025"
lib = unreal.EditorAssetLibrary

if lib.does_asset_exist(DEST):
    raise RuntimeError(f"Refusing to overwrite preserved candidate {DEST}")
if not lib.duplicate_asset(SOURCE, DEST):
    raise RuntimeError("Could not duplicate preserved interactive v024 map")
if not lib.save_asset(DEST, only_if_is_dirty=False):
    raise RuntimeError("Could not save prepared v025 map")

unreal.log(f"LINE_BOSS_PR004_INTERACTIVE_FLOOR_V025_PREPARE_PASS map={DEST}")
unreal.SystemLibrary.quit_editor()
