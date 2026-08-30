"""Open the pre-existing isolated new-press review map for visual comparison only."""

import unreal


TARGET = "/Game/LineBoss/Candidates/PressShop/SquareMeshyPressTrain_v001/Maps/LB_SquareMeshyPressTrain_Review_v010"

if not unreal.EditorAssetLibrary.does_asset_exist(TARGET):
    raise RuntimeError("OPEN_SQUARE_PRESS_REVIEW_V010_FAIL: review map is missing")
if not unreal.EditorLoadingAndSavingUtils.load_map(TARGET):
    raise RuntimeError("OPEN_SQUARE_PRESS_REVIEW_V010_FAIL: Unreal could not open review map")

unreal.log("OPEN_SQUARE_PRESS_REVIEW_V010_PASS=" + TARGET)
