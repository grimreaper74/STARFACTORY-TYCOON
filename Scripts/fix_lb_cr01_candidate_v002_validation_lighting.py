"""Improve neutral validation lighting only; does not alter the LB-CR01 asset."""

import unreal

MAP = "/Game/LineBoss/Developer/Validation/LB_CR01_CleaningAMR_Candidate_v002"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels.load_level(MAP)

for actor in actors.get_all_level_actors():
    label = actor.get_actor_label()
    if label == "LB_CR01_V002_KeyLight":
        component = actor.get_editor_property("directional_light_component")
        component.set_editor_property("intensity", 3.5)
        actor.set_actor_rotation(unreal.Rotator(-35.0, 145.0, 0.0), False)
    elif label == "LB_CR01_V002_SkyLight":
        component = actor.get_editor_property("light_component")
        component.set_editor_property("intensity", 0.8)

existing = {a.get_actor_label() for a in actors.get_all_level_actors()}
fills = (
    ("LB_CR01_V002_Fill_Front", unreal.Vector(260, -260, 260), 120.0, unreal.Color(255, 225, 205, 255)),
    ("LB_CR01_V002_Fill_Rear", unreal.Vector(-220, 220, 190), 80.0, unreal.Color(190, 215, 255, 255)),
)
by_label = {a.get_actor_label(): a for a in actors.get_all_level_actors()}
for label, location, intensity, colour in fills:
    light = by_label.get(label)
    if light is None:
        light = actors.spawn_actor_from_class(unreal.PointLight, location, unreal.Rotator())
        light.set_actor_label(label)
    else:
        light.set_actor_location(location, False, False)
    component = light.get_editor_property("point_light_component")
    component.set_editor_property("intensity", intensity)
    component.set_editor_property("attenuation_radius", 650.0)
    component.set_editor_property("light_color", colour)

if not levels.save_current_level():
    raise RuntimeError("Could not save corrected validation lighting")
unreal.log("LINE_BOSS_LB_CR01_V002_VALIDATION_LIGHTING_PASS")
unreal.SystemLibrary.quit_editor()
