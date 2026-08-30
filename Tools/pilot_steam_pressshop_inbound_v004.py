import unreal

TARGET_LABEL = "Steam wishlist inbound coil handoff"
actors = unreal.EditorLevelLibrary.get_all_level_actors()
camera = next((actor for actor in actors if actor.get_actor_label() == TARGET_LABEL), None)
if camera is None:
    raise RuntimeError("Camera not found: " + TARGET_LABEL)
level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if level_editor is None:
    raise RuntimeError("LevelEditorSubsystem unavailable")
level_editor.pilot_level_actor(camera)
unreal.log("PRESS_SHOP_V004_CAMERA_PASS: viewport set to '{}'".format(TARGET_LABEL))
