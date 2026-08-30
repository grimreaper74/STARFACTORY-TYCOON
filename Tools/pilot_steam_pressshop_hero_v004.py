import unreal

# Native Unreal camera review helper. It only changes the editor viewport;
# it does not alter or save any level/package.
TARGET_LABEL = "Steam wishlist press-line hero"

actors = unreal.EditorLevelLibrary.get_all_level_actors()
camera = next((actor for actor in actors if actor.get_actor_label() == TARGET_LABEL), None)
if camera is None:
    labels = [actor.get_actor_label() for actor in actors if "Steam wishlist" in actor.get_actor_label()]
    raise RuntimeError("Camera not found: {}. Available review cameras: {}".format(TARGET_LABEL, labels))

level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if level_editor is None:
    raise RuntimeError("LevelEditorSubsystem unavailable")
level_editor.pilot_level_actor(camera)
unreal.log("PRESS_SHOP_V004_CAMERA_PASS: viewport set to '{}'".format(TARGET_LABEL))
