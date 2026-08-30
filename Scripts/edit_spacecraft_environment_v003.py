"""edit_spacecraft_environment_v003.py - owner 2026-08-25: "the factory
needs to be a lot bigger". Rescales the floor plane to a 240 x 240 m
hall (the build authority's placement bound grows to 220 m in the same
change set). Walls/apron/sky are rebuilt afterwards by re-running
edit_spacecraft_environment_v001.py then _v002.py (their delete-and-
respawn is keyed to the LB_SC_Env_ label convention).

Run headless (editor closed):
  UnrealEditor-Cmd.exe <proj> -Unattended ... -ExecutePythonScript="<this>"
"""

import unreal

MAP_PATH = ("/Game/LineBoss/Candidates/Spacecraft/SpacecraftFactory_v001"
            "/Maps/LB_SpacecraftFactory_v001")
TARGET_HALF_CM = 12000.0

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not les.load_level(MAP_PATH):
    raise RuntimeError("FAIL CLOSED: could not load " + MAP_PATH)

actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
floor = None
floor_extent = None
for actor in actor_sub.get_all_level_actors():
    if not isinstance(actor, unreal.StaticMeshActor):
        continue
    if actor.get_actor_label().startswith("LB_SC_Env_"):
        continue
    origin, extent = actor.get_actor_bounds(False)
    if (extent.x > 3000 and extent.y > 3000 and extent.z < 200
            and (floor_extent is None or extent.x > floor_extent.x)):
        floor = actor
        floor_extent = extent
if floor is None:
    raise RuntimeError("FAIL CLOSED: no floor-sized StaticMeshActor found")

ratio = TARGET_HALF_CM / floor_extent.x
scale = floor.get_actor_scale3d()
floor.set_actor_scale3d(unreal.Vector(
    scale.x * ratio, scale.y * ratio, scale.z))
unreal.log("FLOOR %s rescaled x%.3f -> half %.0f cm"
           % (floor.get_actor_label(), ratio, TARGET_HALF_CM))

if not les.save_current_level():
    raise RuntimeError("FAIL CLOSED: could not save " + MAP_PATH)
unreal.log("ENVIRONMENT v003 DONE: floor is now a 240 m hall")
