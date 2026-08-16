"""Prepare isolated v026 from the preserved v025 workflow candidate."""

import unreal


SOURCE = "/Game/LineBoss/Maps/LB_PressShop_PR004InteractiveFloorCandidate_v025"
DEST = "/Game/LineBoss/Maps/LB_PressShop_PR004PackagingPolishCandidate_v026"
lib = unreal.EditorAssetLibrary

if lib.does_asset_exist(DEST):
    raise RuntimeError(f"Refusing to overwrite preserved candidate {DEST}")
if not lib.duplicate_asset(SOURCE, DEST):
    raise RuntimeError("Could not duplicate preserved v025 map")
if not lib.save_asset(DEST, only_if_is_dirty=False):
    raise RuntimeError("Could not save prepared v026 map")
unreal.log(f"LINE_BOSS_PR004_PACKAGING_POLISH_V026_PREPARE_PASS map={DEST}")
unreal.SystemLibrary.quit_editor()
