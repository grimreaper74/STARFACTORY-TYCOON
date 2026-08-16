"""Preserve mothballed v004 and create a support-robot placement derivative."""
import unreal

BASE = "/Game/LineBoss/Maps/LB_PressShop_MothballedCandidate_v004"
DEST = "/Game/LineBoss/Maps/LB_PressShop_SupportRobotsCandidate_v005"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
levels.load_level("/Game/LineBoss/Maps/LB_PressShop_Foundation")
if unreal.EditorAssetLibrary.does_asset_exist(DEST):
    raise RuntimeError(f"Refusing to overwrite preserved {DEST}")
if not unreal.EditorAssetLibrary.duplicate_asset(BASE, DEST):
    raise RuntimeError(f"Could not duplicate {BASE}")
if not unreal.EditorAssetLibrary.save_asset(DEST, only_if_is_dirty=False):
    raise RuntimeError(f"Could not save {DEST}")
unreal.log(f"LINE_BOSS_PRESS_V005_PREP_PASS map={DEST}")

