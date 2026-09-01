"""Match LB_SpacecraftFactory_v002's rig to v001's PROVEN values.

The v002 first-guess rig (sun 8lx, no bias) rendered near-black; the
dump of v001 (Saved/Audits/Spacecraft/v001_lighting_dump.json) shows
the values that demonstrably light the site: sun 34lx warm-white at
pitch -55 yaw -135, skylight 2.2, exposure locked 1.0/1.0 with bias
-3.0. Copied, not guessed.
"""
import unreal

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level("/Game/LineBoss/Candidates/Spacecraft/"
               "SpacecraftFactory_v002/Maps/LB_SpacecraftFactory_v002")
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

for actor in eas.get_all_level_actors():
    cls = actor.get_class().get_name()
    if cls == "DirectionalLight":
        actor.set_actor_rotation(
            unreal.Rotator(-55.0, -135.0, 0.0), False)
        c = actor.get_component_by_class(unreal.DirectionalLightComponent)
        c.set_editor_property("intensity", 34.0)
        c.set_editor_property(
            "light_color", unreal.Color(r=255, g=246, b=232, a=255))
    elif cls == "SkyLight":
        c = actor.get_component_by_class(unreal.SkyLightComponent)
        c.set_editor_property("intensity", 2.2)
    elif cls == "PostProcessVolume":
        s = actor.get_editor_property("settings")
        s.set_editor_property("override_auto_exposure_bias", True)
        s.set_editor_property("auto_exposure_bias", -3.0)
        actor.set_editor_property("settings", s)

if les.save_current_level():
    unreal.log("V002 LIGHTING MATCHED TO V001 PROVEN RIG")
else:
    unreal.log_error("SAVE FAILED")
