"""Set the native Unreal viewport to the clean 2126 Press Shop hero review."""
import math
import unreal

MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("PRESSSHOP_2126_HERO_FAIL: map did not load")

# Camera sits inside the sparse perimeter structure. It keeps the open-bay
# framing but does not look through a foreground forest of columns.
camera = unreal.Vector(-24800.0, -21400.0, 10800.0)
target = unreal.Vector(4700.0, 0.0, 1900.0)
dx, dy, dz = target.x - camera.x, target.y - camera.y, target.z - camera.z
flat = math.sqrt(dx * dx + dy * dy)
rotation = unreal.Rotator(pitch=math.degrees(math.atan2(dz, flat)), yaw=math.degrees(math.atan2(dy, dx)), roll=0.0)
unreal.EditorLevelLibrary.set_level_viewport_camera_info(camera, rotation)
unreal.log("PRESSSHOP_2126_HERO_PASS")
