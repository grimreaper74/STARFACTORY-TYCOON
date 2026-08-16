"""Duplicate the v001 preview map without switching worlds in-process.

UE 5.8's unattended editor can retain the old world when a Python script
duplicates and then loads a map in the same process.  This first stage only
creates and saves the v002 package; a separate process opens it directly.
"""

import unreal


SOURCE = "/Game/LineBoss/Developer/Validation/LB_SupportRobot_Materials_Candidate_v001"
DEST = "/Game/LineBoss/Developer/Validation/LB_SupportRobot_Materials_Candidate_v002"
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

unreal.log(f"LINE_BOSS_SUPPORT_ROBOT_MATERIAL_PREVIEW_V002_DUPLICATE_PASS dest={DEST}")
unreal.SystemLibrary.quit_editor()
