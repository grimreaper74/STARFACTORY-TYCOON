"""Pilot the editor viewport for an unsaved close visual review of the carrier."""
import math
import unreal


unreal.EditorLevelLibrary.eject_pilot_level_actor()
source = unreal.Vector(750.0, -1050.0, 430.0)
target = unreal.Vector(1350.0, 0.0, 145.0)
dx, dy, dz = target.x - source.x, target.y - source.y, target.z - source.z
horizontal = math.sqrt(dx * dx + dy * dy)
rotation = unreal.Rotator(math.degrees(math.atan2(dz, horizontal)), math.degrees(math.atan2(dy, dx)), 0.0)
unreal.EditorLevelLibrary.set_level_viewport_camera_info(source, rotation)
unreal.log("INDUCTION_CARRIER_PILOT_VIEW_READY")
