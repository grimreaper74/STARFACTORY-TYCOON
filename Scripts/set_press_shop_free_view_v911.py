import unreal

# Building plan is 220 m east-west by 120 m north-south.
# Place the editor camera high above the centre, angled along the full shop.
location = unreal.Vector(11000.0, 6000.0, 24000.0)
rotation = unreal.Rotator(-67.0, -135.0, 0.0)
unreal.EditorLevelLibrary.set_level_viewport_camera_info(location, rotation)
unreal.log('LINE_BOSS_PRESS_SHOP_FREE_VIEW_V911_SET')
