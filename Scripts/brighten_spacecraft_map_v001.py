"""brighten_spacecraft_map_v001.py - the owner played the slice map and
it is far too dark ("clean futuristic industrial, strong clean lighting"
is the settled direction). Loads LB_SpacecraftFactory_v001, reports the
existing lights, raises them to a bright clean-industrial baseline and
pins exposure so auto-adaptation cannot sink the floor back into the
dark. Saves the map; receipt note goes in the StationMeshes receipt.

Run headless (editor closed):
  UnrealEditor-Cmd.exe <proj> -Unattended ... -ExecutePythonScript="<this>"
"""

import unreal

MAP_PATH = ("/Game/LineBoss/Candidates/Spacecraft/SpacecraftFactory_v001"
            "/Maps/LB_SpacecraftFactory_v001")

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not les.load_level(MAP_PATH):
    raise RuntimeError("FAIL CLOSED: could not load " + MAP_PATH)

actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actors = actor_sub.get_all_level_actors()

found = {"directional": 0, "sky": 0, "post": 0}
for actor in actors:
    if isinstance(actor, unreal.DirectionalLight):
        comp = actor.get_component_by_class(
            unreal.DirectionalLightComponent)
        old = comp.intensity
        comp.set_editor_property("intensity", 8.0)  # bright clean lux
        comp.set_editor_property("light_color",
                                 unreal.Color(255, 250, 244))
        found["directional"] += 1
        unreal.log("DIRECTIONAL %s: %.2f -> 8.0 lux"
                   % (actor.get_actor_label(), old))
    elif isinstance(actor, unreal.SkyLight):
        comp = actor.get_component_by_class(unreal.SkyLightComponent)
        old = comp.intensity
        comp.set_editor_property("intensity", 2.0)
        found["sky"] += 1
        unreal.log("SKYLIGHT %s: %.2f -> 2.0" %
                   (actor.get_actor_label(), old))
    elif isinstance(actor, unreal.PostProcessVolume):
        settings = actor.get_editor_property("settings")
        settings.set_editor_property("override_auto_exposure_min_brightness",
                                     True)
        settings.set_editor_property("override_auto_exposure_max_brightness",
                                     True)
        settings.set_editor_property("auto_exposure_min_brightness", 1.0)
        settings.set_editor_property("auto_exposure_max_brightness", 1.0)
        actor.set_editor_property("settings", settings)
        found["post"] += 1
        unreal.log("POSTPROCESS %s: exposure pinned to 1.0"
                   % actor.get_actor_label())

# No post-process volume in the map: add an unbound one that pins
# exposure, so the bright baseline is what the player actually sees.
if found["post"] == 0:
    ppv = actor_sub.spawn_actor_from_class(
        unreal.PostProcessVolume, unreal.Vector(0, 0, 0))
    ppv.set_actor_label("LB_Spacecraft_ExposurePin")
    ppv.set_editor_property("unbound", True)
    settings = ppv.get_editor_property("settings")
    settings.set_editor_property("override_auto_exposure_min_brightness",
                                 True)
    settings.set_editor_property("override_auto_exposure_max_brightness",
                                 True)
    settings.set_editor_property("auto_exposure_min_brightness", 1.0)
    settings.set_editor_property("auto_exposure_max_brightness", 1.0)
    ppv.set_editor_property("settings", settings)
    found["post"] += 1
    unreal.log("POSTPROCESS added unbound exposure pin")

if found["directional"] == 0:
    raise RuntimeError("FAIL CLOSED: no DirectionalLight in the map - "
                       "inspect before inventing lighting")

if not les.save_current_level():
    raise RuntimeError("FAIL CLOSED: could not save " + MAP_PATH)
unreal.log("MAP BRIGHTEN DONE: %s" % found)
