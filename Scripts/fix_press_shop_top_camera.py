"""Repair the foundation's fixed top-down camera orientation."""

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_Foundation"
CAMERA = "LB_CAM_PressShop_TopDown"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels.load_level(MAP)
camera = next((actor for actor in actors.get_all_level_actors() if actor.get_actor_label() == CAMERA), None)
if camera is None:
    raise RuntimeError(f"Missing {CAMERA}")
camera.set_actor_location(unreal.Vector(0.0, 0.0, 26000.0), False, False)
# Python's Rotator constructor order is roll, pitch, yaw.  Roll the downward
# camera so the 220 m east-west building axis uses the 16:9 frame width.
camera.set_actor_rotation(unreal.Rotator(90.0, -90.0, 0.0), False)
component = camera.get_editor_property("camera_component")
component.set_editor_property("projection_mode", unreal.CameraProjectionMode.ORTHOGRAPHIC)
component.set_editor_property("ortho_width", 25000.0)
if not levels.save_current_level():
    raise RuntimeError("Failed saving repaired top-down camera")
unreal.log("LINE_BOSS_PRESS_SHOP_TOP_CAMERA_FIX_PASS")
