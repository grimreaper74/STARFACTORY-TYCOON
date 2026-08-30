"""brighten_spacecraft_map_v002.py - supersedes v001. The v001 pass
raised intensities but the owner still saw silhouettes: the SkyLight
captures the scene for ambient, and this map has NO sky, so ambient is
black and every face not pointing at the sun renders dark. This pass
switches the SkyLight to a specified engine grey cubemap (constant
ambient from all directions - the clean-industrial baseline) and leaves
the v001 sun and exposure pin in place.

Run headless (editor closed):
  UnrealEditor-Cmd.exe <proj> -Unattended ... -ExecutePythonScript="<this>"
"""

import unreal

MAP_PATH = ("/Game/LineBoss/Candidates/Spacecraft/SpacecraftFactory_v001"
            "/Maps/LB_SpacecraftFactory_v001")
CUBEMAP = "/Engine/EngineResources/GrayLightTextureCube"

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not les.load_level(MAP_PATH):
    raise RuntimeError("FAIL CLOSED: could not load " + MAP_PATH)

cube = unreal.EditorAssetLibrary.load_asset(CUBEMAP)
if cube is None:
    raise RuntimeError("FAIL CLOSED: engine cubemap missing: " + CUBEMAP)

actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
fixed = 0
for actor in actor_sub.get_all_level_actors():
    if isinstance(actor, unreal.SkyLight):
        comp = actor.get_component_by_class(unreal.SkyLightComponent)
        comp.set_editor_property("source_type",
                                 unreal.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP)
        comp.set_editor_property("cubemap", cube)
        comp.set_editor_property("intensity", 3.0)
        comp.set_editor_property("mobility",
                                 unreal.ComponentMobility.MOVABLE)
        fixed += 1
        unreal.log("SKYLIGHT %s: specified grey cubemap, intensity 3.0"
                   % actor.get_actor_label())

if fixed == 0:
    raise RuntimeError("FAIL CLOSED: no SkyLight in the map")
if not les.save_current_level():
    raise RuntimeError("FAIL CLOSED: could not save " + MAP_PATH)
unreal.log("MAP BRIGHTEN v002 DONE: %d skylight(s) on constant ambient"
           % fixed)
