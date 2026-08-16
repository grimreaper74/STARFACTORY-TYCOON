"""Stabilize LB-CR01 evidence exposure without changing imported asset materials."""

import unreal

MAP = "/Game/LineBoss/Developer/Validation/LB_CR01_CleaningAMR_Candidate_v002"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels.load_level(MAP)

for actor in list(actors.get_all_level_actors()):
    label = actor.get_actor_label()
    if label.startswith("LB_CR01_V002_Fill_"):
        actors.destroy_actor(actor)
    elif label == "LB_CR01_V002_KeyLight":
        component = actor.get_editor_property("directional_light_component")
        component.set_editor_property("intensity", 4.0)
        actor.set_actor_rotation(unreal.Rotator(-42.0, -35.0, 0.0), False)
    elif label == "LB_CR01_V002_SkyLight":
        component = actor.get_editor_property("light_component")
        component.set_editor_property("intensity", 0.9)
    elif label.startswith("LB_CR01_V002_CAM_"):
        component = actor.get_editor_property("camera_component")
        component.set_editor_property("post_process_blend_weight", 1.0)
        settings = component.get_editor_property("post_process_settings")
        settings.set_editor_property("override_auto_exposure_min_brightness", True)
        settings.set_editor_property("override_auto_exposure_max_brightness", True)
        settings.set_editor_property("override_auto_exposure_bias", True)
        settings.set_editor_property("auto_exposure_min_brightness", 1.0)
        settings.set_editor_property("auto_exposure_max_brightness", 1.0)
        settings.set_editor_property("auto_exposure_bias", 1.25)
        component.set_editor_property("post_process_settings", settings)

if not levels.save_current_level():
    raise RuntimeError("Could not save stabilized LB-CR01 evidence map")
unreal.log("LINE_BOSS_LB_CR01_V002_EVIDENCE_STABILIZE_PASS")
