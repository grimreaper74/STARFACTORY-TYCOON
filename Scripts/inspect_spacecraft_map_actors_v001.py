"""List every actor in the spacecraft map - what does a player actually
inherit at first launch? The owner's words: "its unplayble, already
stuff in map". Read-only."""
import unreal
world = unreal.EditorLoadingAndSavingUtils.load_map(
    "/Game/LineBoss/Candidates/Spacecraft/SpacecraftFactory_v001/Maps/"
    "LB_SpacecraftFactory_v001")
actors = unreal.EditorLevelLibrary.get_all_level_actors()
counts = {}
for actor in actors:
    key = actor.get_class().get_name()
    counts.setdefault(key, []).append(actor.get_actor_label())
for key in sorted(counts, key=lambda k: -len(counts[k])):
    names = counts[key]
    sample = ", ".join(names[:4])
    print("ACTORCLASS %s x%d: %s%s" % (key, len(names), sample,
          " ..." if len(names) > 4 else ""))
