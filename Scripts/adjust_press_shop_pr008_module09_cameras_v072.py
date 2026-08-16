"""Apply the reviewed, aisle-clear fixed cameras to retained Module 09 v072."""
import unreal

MAP = "/Game/LineBoss/Maps/LB_PressShop_PR008Module09Candidate_v072"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

updates = {
    "LB_PR008_V072_CAM_Module09Inspection": ((-360, -2620, 285), (-95, -2205, 110), 42),
    "LB_PR008_V072_CAM_Module09RearService": ((230, -2500, 280), (-95, -2205, 110), 45),
    "LB_PR008_V072_CAM_Module09Elevated": ((-520, -2720, 560), (-95, -2205, 110), 52),
}
actors = {actor.get_actor_label(): actor for actor in actors_api.get_all_level_actors()}
for label, (location, target, fov) in updates.items():
    actor = actors.get(label)
    if not isinstance(actor, unreal.CameraActor):
        raise RuntimeError(f"Missing authored Module 09 camera {label}")
    actor.set_actor_location(unreal.Vector(*location), False, False)
    actor.set_actor_rotation(
        unreal.MathLibrary.find_look_at_rotation(actor.get_actor_location(), unreal.Vector(*target)), False)
    actor.camera_component.set_editor_property("field_of_view", fov)

if not levels.save_current_level():
    raise RuntimeError(f"Could not save camera corrections to {MAP}")
unreal.log("LINE_BOSS_PR008_V072_CAMERA_ADJUST_PASS__AISLE_CLEAR_FIXED_VIEWS")
unreal.SystemLibrary.quit_editor()
