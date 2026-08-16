"""Read-only transform inspection for the failed v009 PR-004 console mount."""

import unreal


MAP = "/Game/LineBoss/Maps/LB_MainControlRoom_PR004ConsoleCandidate_v009"
unreal.EditorLoadingAndSavingUtils.load_map(MAP)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for actor in actors_api.get_all_level_actors():
    if actor.get_actor_label() == "LB_MCR_V009_PR004_AuthorityConsole":
        print({
            "label": actor.get_actor_label(),
            "location": str(actor.get_actor_location()),
            "rotation": str(actor.get_actor_rotation()),
            "scale": str(actor.get_actor_scale3d()),
        })
