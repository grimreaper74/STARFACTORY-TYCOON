"""Open the roofless Press Shop Steam composition candidate for visual review only."""

import unreal


TARGET = "/Game/LineBoss/Candidates/PressShop/SquareMeshyPressTrain_v001/Maps/LB_PressShop_SteamComposition_v002"

if not unreal.EditorAssetLibrary.does_asset_exist(TARGET):
    raise RuntimeError("OPEN_STEAM_COMPOSITION_V002_FAIL: candidate map is missing")
if not unreal.EditorLoadingAndSavingUtils.load_map(TARGET):
    raise RuntimeError("OPEN_STEAM_COMPOSITION_V002_FAIL: Unreal could not open candidate")

unreal.log("OPEN_STEAM_COMPOSITION_V002_PASS=" + TARGET)
