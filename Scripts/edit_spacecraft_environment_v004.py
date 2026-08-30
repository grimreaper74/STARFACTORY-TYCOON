"""edit_spacecraft_environment_v004.py - stage lighting. The player
camera looks north-east, so it photographs every building's SOUTH-WEST
faces - and the sun sat in the north-east, lighting only the backs
("models aren't rendering full detail" was one third this). Swing the
key light to the camera's side of the sky and lift the ambient fill.

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
suns = 0
skies = 0
for actor in actor_sub.get_all_level_actors():
    if isinstance(actor, unreal.DirectionalLight):
        # Key from the south-west, high enough for short crisp shadows.
        actor.set_actor_rotation(
            unreal.Rotator(pitch=-55.0, yaw=225.0, roll=0.0), False)
        comp = actor.get_component_by_class(
            unreal.DirectionalLightComponent)
        comp.set_editor_property("intensity", 10.0)
        suns += 1
        unreal.log("SUN keyed from the south-west at 10 lux")
    elif isinstance(actor, unreal.SkyLight):
        comp = actor.get_component_by_class(unreal.SkyLightComponent)
        comp.set_editor_property("intensity", 3.2)
        skies += 1
        unreal.log("SKYLIGHT fill raised to 3.2")

if suns == 0 or skies == 0:
    raise RuntimeError("FAIL CLOSED: lighting actors missing")
if not les.save_current_level():
    raise RuntimeError("FAIL CLOSED: could not save " + MAP_PATH)
unreal.log("ENVIRONMENT v004 DONE: key light faces the player")
