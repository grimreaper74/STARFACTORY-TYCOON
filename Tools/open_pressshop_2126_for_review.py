"""Open the fresh 2126 Press Shop candidate at its authored hero-review angle.

This is intentionally view-only: it does not save, alter, or load any protected
production map.  It is used from Unreal's native Execute Python Script command.
"""

import unreal


MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
CAMERA = unreal.Vector(-14500.0, -19500.0, 6800.0)
TARGET = unreal.Vector(-300.0, 0.0, 2300.0)

unreal.EditorLoadingAndSavingUtils.load_map(MAP)
rotation = unreal.MathLibrary.find_look_at_rotation(CAMERA, TARGET)
unreal.EditorLevelLibrary.set_level_viewport_camera_info(CAMERA, rotation)
unreal.log("PRESSSHOP_2126_REVIEW_MAP_OPENED__VIEW_ONLY")
