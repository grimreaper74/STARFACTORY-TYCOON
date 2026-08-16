"""Tune only the HMI v004 validation stage; does not touch source meshes."""

import unreal

MAP = "/Game/LineBoss/Developer/Validation/LB_HMI04_ModelingValidation"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels.load_level(MAP)

for actor in actors.get_all_level_actors():
    label = actor.get_actor_label()
    if label == "LB_HMI04_Key":
        actor.get_editor_property("directional_light_component").set_editor_property("intensity", 3.0)
    elif label == "LB_HMI04_Fill":
        actor.get_editor_property("rect_light_component").set_editor_property("intensity", 500.0)
    elif label == "LB_HMI04_FixedExposure":
        actor.set_editor_property("blend_weight", 0.0)
    elif label == "LB_CAM_HMI04_Front":
        actor.set_actor_location(unreal.Vector(170, 270, 132), False, False)
        actor.set_actor_rotation(
            unreal.MathLibrary.find_look_at_rotation(actor.get_actor_location(), unreal.Vector(0, 0, 78)),
            False,
        )
        component = actor.get_editor_property("camera_component")
        component.set_editor_property("post_process_blend_weight", 0.0)

levels.save_current_level()
unreal.log("LINE_BOSS_HMI04_VALIDATION_TUNED")
