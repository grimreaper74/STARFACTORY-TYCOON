"""Remove only generated LB-CR01 v001 Unreal assets in an isolated session."""

import unreal

DEST = "/Game/LineBoss/Shared/SupportRobots/LB_CR01/Candidate_v001"
MAP = "/Game/LineBoss/Developer/Validation/LB_CR01_CleaningAMR_Candidate_v001"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
levels.load_level("/Game/LineBoss/Maps/LB_PressShop_Foundation")
if unreal.EditorAssetLibrary.does_asset_exist(MAP):
    if not unreal.EditorAssetLibrary.delete_asset(MAP):
        raise RuntimeError(f"Could not remove generated map {MAP}")
if unreal.EditorAssetLibrary.does_directory_exist(DEST):
    if not unreal.EditorAssetLibrary.delete_directory(DEST):
        raise RuntimeError(f"Could not remove generated import folder {DEST}")
unreal.log("LINE_BOSS_LB_CR01_V001_CLEAN_PASS")
