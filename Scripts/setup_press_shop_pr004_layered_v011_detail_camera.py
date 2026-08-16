"""Add the known v009 authored-detail camera to the isolated v011 map."""
import unreal
MAP="/Game/LineBoss/Maps/LB_PressShop_PR004LayeredMaterialCandidate_v011"
LABEL="LB_AUDIT_PR004_RobotAuthoredDetails_v009"
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP): raise RuntimeError(f"Could not load {MAP}")
camera=next((a for a in actors.get_all_level_actors() if a.get_actor_label()==LABEL),None)
if camera is None:
 camera=actors.spawn_actor_from_class(unreal.CameraActor,unreal.Vector(-5300.0,-1200.0,470.0)); camera.set_actor_label(LABEL)
camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(),unreal.Vector(-4700.0,-2150.0,155.0)),False)
camera.camera_component.set_editor_property("field_of_view",46.0)
if not levels.save_current_level(): raise RuntimeError("Could not save v011 camera")
unreal.log("LINE_BOSS_PR004_LAYERED_V011_CAMERA_PASS")
unreal.SystemLibrary.quit_editor()
