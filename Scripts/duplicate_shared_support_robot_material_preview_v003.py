"""Create a v003 preview-map package without an in-process map switch."""

import unreal


SOURCE = "/Game/LineBoss/Developer/Validation/LB_SupportRobot_Materials_Candidate_v002"
DEST = "/Game/LineBoss/Developer/Validation/LB_SupportRobot_Materials_Candidate_v003"
lib = unreal.EditorAssetLibrary

if not lib.does_asset_exist(SOURCE):
    raise RuntimeError(f"Missing source map {SOURCE}")
if lib.does_asset_exist(DEST):
    raise RuntimeError(f"Refusing to overwrite existing destination {DEST}")
if lib.duplicate_asset(SOURCE, DEST) is None:
    raise RuntimeError(f"Could not duplicate {SOURCE} to {DEST}")
if not lib.save_asset(DEST, only_if_is_dirty=False):
    raise RuntimeError(f"Could not save {DEST}")
if not lib.does_asset_exist(DEST):
    raise RuntimeError(f"Destination did not survive save: {DEST}")

unreal.log(f"LINE_BOSS_SUPPORT_ROBOT_MATERIAL_PREVIEW_V003_DUPLICATE_PASS dest={DEST}")
unreal.SystemLibrary.quit_editor()
