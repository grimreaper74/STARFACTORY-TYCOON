"""Create a reusable candidate-only close camera for the induction carrier."""
import unreal


LABEL = "Steam wishlist induction coil carrier detail"
# Same exterior-safe pose as the already proven inbound story camera.  We only
# change its field of view and label so the sky-field shell cannot occlude the
# review image by placing the eye inside it.
source = unreal.Vector(-900.0, -5800.0, 1500.0)
rotation = unreal.Rotator(-11.05, 83.61, 0.0)

actors = unreal.EditorLevelLibrary.get_all_level_actors()
camera = next((actor for actor in actors if actor.get_actor_label() == LABEL), None)
if camera is None:
    camera = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.CameraActor, source, rotation)
    if camera is None:
        raise RuntimeError("Could not create induction carrier review camera")
    camera.set_actor_label(LABEL)
    camera.tags = [unreal.Name("LB.PressShop.SteamOpenBay.v004"), unreal.Name("LB.PressShop.Camera"), unreal.Name("LB.Future2126.GuidedCarrier")]
    camera.camera_component.set_editor_property("field_of_view", 50.0)
else:
    camera.set_actor_location_and_rotation(source, rotation, False, False)
if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save candidate review camera")

level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if level_editor is None:
    raise RuntimeError("LevelEditorSubsystem unavailable")
level_editor.pilot_level_actor(camera)
unreal.log("INDUCTION_CARRIER_CAMERA_READY=" + LABEL)
