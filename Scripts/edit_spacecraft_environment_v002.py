"""edit_spacecraft_environment_v002.py - supersedes nothing, extends
v001: the owner's screenshot shows a BLACK void above the walls. Adds a
SkyAtmosphere (so the world outside the factory reads as sky), marks the
sun as an atmosphere light, and adds gentle height fog for depth.
Idempotent via the LB_SC_Env_ label convention. Saves the map.

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

for actor in list(actors):
    if actor.get_actor_label() in ("LB_SC_Env_SkyAtmosphere",
                                   "LB_SC_Env_HeightFog"):
        actor_sub.destroy_actor(actor)

sky = actor_sub.spawn_actor_from_class(
    unreal.SkyAtmosphere, unreal.Vector(0, 0, 0))
sky.set_actor_label("LB_SC_Env_SkyAtmosphere")

fog = actor_sub.spawn_actor_from_class(
    unreal.ExponentialHeightFog, unreal.Vector(0, 0, 0))
fog.set_actor_label("LB_SC_Env_HeightFog")
fog_comp = fog.get_component_by_class(unreal.ExponentialHeightFogComponent)
fog_comp.set_editor_property("fog_density", 0.006)
fog_comp.set_editor_property("fog_height_falloff", 0.3)

suns = 0
for actor in actor_sub.get_all_level_actors():
    if isinstance(actor, unreal.DirectionalLight):
        comp = actor.get_component_by_class(
            unreal.DirectionalLightComponent)
        comp.set_editor_property("atmosphere_sun_light", True)
        suns += 1
if suns == 0:
    raise RuntimeError("FAIL CLOSED: no DirectionalLight to drive the sky")

if not les.save_current_level():
    raise RuntimeError("FAIL CLOSED: could not save " + MAP_PATH)
unreal.log("ENVIRONMENT v002 DONE: sky atmosphere + fog, %d sun(s)" % suns)
